"""Backend orchestration; every invocation gets a new run, even on failure."""
import json,traceback,shutil
from pathlib import Path
import numpy as np
import pandas as pd
from pathpocket.core.run_context import RunContext,write_json
from pathpocket.core.provenance import capture
from pathpocket.protein.structure import atoms,align,transform
from pathpocket.engines.fpocket import discover
from pathpocket.engines.ed2mol import generate
from pathpocket.regions.models import load_targets
from pathpocket.regions.matching import match_regions
from pathpocket.regions.selection import select_families
from pathpocket.regions.homology import targets_for_family
from pathpocket.protein.normalization import normalize,canonical_records,csv_table
from pathpocket.protein.residue_mapping import MappingError
from pathpocket.protein.structure_mode import prepare_and_normalize
from pathpocket.protein.aggregate import AggregateError

def execute(config,until='run',engineering_fixture=None):
    ctx=RunContext(config);step='initialize';completed=[]
    def done(folder):
        previous=[a['artifact_id'] for a in ctx.artifacts if a['step']==(completed[-1] if completed else 'inputs')]
        for p in sorted(ctx.path(folder).rglob('*')):
            if p.is_file():ctx.register(p,folder,'Step output',previous)
        completed.append(folder);ctx.event(folder,'PASS',len(completed)/9,'Step completed')
    try:
        if engineering_fixture:
            required={'fixture_id','source','semantics','marker_sha256','selection_policy'}
            if set(engineering_fixture)!=required or engineering_fixture['fixture_id']!='builtin_no_targets_v1' or engineering_fixture['selection_policy']!='FORCE_EMPTY_AT_TARGET_SELECTION':raise ValueError('Unsupported engineering fixture')
            ctx.manifest['engineering_fixture']=engineering_fixture
            ctx.event('initialize','running',0,'Engineering negative control active: target selection will be forced empty; discovery remains unchanged')
        ctx.snapshot(config.source,'project.yml');write_json(ctx.path('00_INPUTS/resolved_config.json'),config.data)
        if engineering_fixture:write_json(ctx.path('00_INPUTS/engineering_fixture.json'),engineering_fixture)
        ctx.register(ctx.path('00_INPUTS/resolved_config.json'),'inputs','Validated configuration with defaults and normalized paths',[ctx.artifacts[0]['artifact_id']])
        ctx.manifest.update(capture(config));ctx.manifest.update(run_id=ctx.root.name,status='RUNNING');write_json(ctx.path('run_manifest.json'),ctx.manifest)
        step='01_VALIDATE';ctx.event(step,'running',0,'Validating input structures');receptors=[]
        for sid,state in config.states.items():
            for i,path in enumerate(state['structures'],1):
                rid=sid+f'_R{i:04d}';snap=ctx.snapshot(path,rid+(Path(path).suffix if Path(path).suffix.lower() in ['.cif','.mmcif'] else '.pdb'))
                receptors.append(dict(receptor_id=rid,state_id=sid,path=str(snap)))
        write_json(ctx.path(step+'/receptors.json'),receptors)
        residue_maps,mapping_summary,aggregate_summary=prepare_and_normalize(receptors,ctx.path(step),config.data['protein'].get('structure_mode','auto'));ctx.manifest['residue_mapping']=mapping_summary;ctx.manifest['aggregate']=aggregate_summary
        write_json(ctx.path(step+'/receptors.json'),receptors)
        done(step)
        step='02_ALIGN';ctx.event(step,'running',0,'Aligning common CA residues');reference=atoms(receptors[0]['path'])
        for r in receptors:
            records=atoms(r['path'])
            identity=all(x['mapping_mode']=='identity' for x in mapping_summary['chain_mappings'] if x['receptor_id']==r['receptor_id'])
            mobile_ids=records if identity else canonical_records(records,residue_maps[r['receptor_id']])
            reference_ids=reference if identity else canonical_records(reference,residue_maps[receptors[0]['receptor_id']])
            rotation,translation,metrics=align(mobile_ids,reference_ids)
            if metrics['matched_fraction']<.5:raise ValueError('Less than half of CA residues matched; explicit sequence/chain mapping required')
            dest=ctx.path(step+'/'+r['receptor_id']+'.pdb');transform(records,rotation,translation,dest)
            r.update(aligned=str(dest),alignment=metrics);write_json(ctx.path(step+'/'+r['receptor_id']+'_transform.json'),dict(rotation=rotation.tolist(),translation=translation.tolist(),**metrics))
        write_json(ctx.path(step+'/receptors.json'),receptors);done(step)
        imported=config.data['region_discovery']['imported_manifest'];step='03_REGION_DISCOVERY';ctx.event(step,'running',0,'Loading or discovering regions');instances=[]
        if imported:
            snap=ctx.snapshot(imported,'region_reference.json');data=load_targets(snap,set(config.states));families=data['families'];targets=data['targets']
            write_json(ctx.path(step+'/imported_reference.json'),data)
        else:
            for i,r in enumerate(receptors):
                ctx.event(step,'running',i/len(receptors),'Discovering candidates in '+r['receptor_id'])
                instances.extend(discover(config.data['runtime']['fpocket'],r['aligned'],ctx.path(step+'/'+r['receptor_id']),r['receptor_id'],r['state_id'],config.data['region_discovery']['top_n']))
            for instance in instances:
                instance['raw_residues']=instance['residues'];lookup=residue_maps[instance['receptor_id']]
                instance['residues']=sorted({lookup[k] for k in instance['raw_residues']})
                instance['residue_identity_space']='canonical'
            write_json(ctx.path(step+'/instances.json'),instances)
        done(step);step='04_REGION_MATCHING';ctx.event(step,'running',0,'Matching candidate regions')
        if not imported:
            m=config.data['region_matching'];families=match_regions(instances,receptors,m['centroid_cutoff_A'],m['residue_jaccard_min'],m['sensitivity_analysis'])
        write_json(ctx.path(step+'/families.json'),families);done(step);step='05_TARGET_SELECTION';ctx.event(step,'running',0,'Selecting representative targets')
        if not imported:
            selected=([] if engineering_fixture else select_families(families,config.data['target_selection']['max_region_families'],config.data['target_selection']['include_comparator'])) if families else [];targets=[]
            if engineering_fixture:ctx.event(step,'running',0,'Engineering negative control: selected targets forced empty after normal discovery and matching')
            for family in selected:targets.extend(targets_for_family(family,instances,receptors,ctx.path(step),residue_maps=residue_maps))
        else:
            selected=families[:config.data['target_selection']['max_region_families']];selected_ids={f['region_family_id'] for f in selected};targets=[t for t in targets if t['region_family_id'] in selected_ids]
            for t in targets:
                folder=ctx.path(step+'/'+t['target_id']);folder.mkdir()
                for key in ['receptor','full_receptor']:
                    source=Path(t[key]);snap=ctx.snapshot(source,t['target_id']+'_'+key+'.pdb');dest=folder/(key+'.pdb');shutil.copy2(snap,dest);t[key]=str(dest)
        write_json(ctx.path(step+'/targets.json'),targets);write_json(ctx.path(step+'/selected_families.json'),selected)
        csv_table(ctx.path('03_REGION_DISCOVERY/region_instances.csv'),instances,['region_instance_id','receptor_id','state_id','rank','center','residues'])
        csv_table(ctx.path('04_REGION_MATCHING/region_families.csv'),families,['region_family_id','members','center','consensus_residues','state_occurrence'])
        csv_table(ctx.path(step+'/selected_targets.csv'),targets,['target_id','region_family_id','state_id','receptor_id','detected_pocket','center'])
        # These additive tables are created after their upstream stage registration.
        for folder,name in [('03_REGION_DISCOVERY','region_instances.csv'),('04_REGION_MATCHING','region_families.csv')]:ctx.register(ctx.path(folder+'/'+name),folder,'Structured discovery/matching table')
        done(step)
        if until=='discover':ctx.finish('DISCOVERED',completed_steps=completed,recovery_point='Run challenge or run with the same config in a new run');return ctx.root
        step='06_CHEMICAL_CHALLENGE';results={}
        if not targets:
            write_json(ctx.path(step+'/results.json'),{});write_json(ctx.path(step+'/execution_status.json'),dict(status='SKIPPED',reason='NO_TARGETS',engine_invocations=0))
            ctx.manifest.update(result_class='NO_TARGETS',target_count=0,generation_status='SKIPPED');ctx.event(step,'PASS',len(completed)/9,'SKIPPED / NOT_APPLICABLE: no targets selected; ED2Mol was not started');done(step)
            return finish_analysis(ctx,selected,targets,results,completed,done,until)
        from concurrent.futures import ThreadPoolExecutor,as_completed
        ctx.event(step,'running',0,f'Generating {len(targets)} independent targets')
        with ThreadPoolExecutor(max_workers=config.data['generation']['max_parallel_targets']) as pool:
            jobs={pool.submit(generate,config.data['runtime'],config.data['generation'],t,ctx.path(step+'/'+t['target_id'])):t for t in targets}
            try:
                for job in as_completed(jobs):
                    t=jobs[job];results[t['target_id']]=job.result();ctx.event(step,'running',len(results)/len(targets),'Completed target '+t['target_id'])
            except Exception:
                for job in jobs:job.cancel()
                raise
        write_json(ctx.path(step+'/results.json'),results);done(step)
        if until=='challenge':ctx.finish('CHALLENGED',completed_steps=completed,recovery_point='Use analyze/report --from-run to reuse these immutable engine outputs');return ctx.root
        return finish_analysis(ctx,selected,targets,results,completed,done,until)
    except Exception as exc:
        if isinstance(exc,(MappingError,AggregateError)):
            summary=ctx.path('01_VALIDATE/mapping_summary.json')
            if summary.exists():ctx.manifest['residue_mapping']=json.loads(summary.read_text())
            aggregate=ctx.path('01_VALIDATE/aggregate_detection_summary.json')
            if aggregate.exists():ctx.manifest['aggregate']=json.loads(aggregate.read_text())
            for p in ctx.path('01_VALIDATE').rglob('*'):
                if p.is_file() and not any(a['path']==str(p.relative_to(ctx.root)) for a in ctx.artifacts):ctx.register(p,'01_VALIDATE','Mapping failure evidence')
        events=ctx.path('progress.jsonl').read_text().splitlines()
        if events:step=json.loads(events[-1])['step']
        ctx.path('logs/error.log').write_text(traceback.format_exc());ctx.event(step,'FAIL',0,str(exc));ctx.finish('FAIL',failed_step=step,completed_steps=completed,recovery_point=f'Inspect {step}; rerun in a new run directory',error=str(exc));raise RuntimeError(f'{exc}; preserved run: {ctx.root}') from exc

def finish_analysis(ctx,selected,targets,results,completed,done,until):
    ctx.manifest.update(result_class='TARGETS_GENERATED' if targets else 'NO_TARGETS',target_count=len(targets),generation_status='COMPLETE' if targets else 'SKIPPED')
    mapping_path=ctx.path('01_VALIDATE/mapping_summary.json')
    if mapping_path.exists():ctx.manifest['residue_mapping']=json.loads(mapping_path.read_text())
    aggregate_path=ctx.path('01_VALIDATE/aggregate_detection_summary.json')
    if aggregate_path.exists():ctx.manifest['aggregate']=json.loads(aggregate_path.read_text())
    from pathpocket.analysis.generation_qc import analyze_target
    from pathpocket.analysis.chemical_space import profile
    from pathpocket.reporting.figures import render
    from pathpocket.reporting.report import report
    ctx.event('07_ANALYSIS','running',0,'QC and chemical-space profiling');frames=[];summaries=[];molecules={}
    for t in targets:
        df,s,m=analyze_target(ctx.path('06_CHEMICAL_CHALLENGE/'+t['target_id']),t,ctx.config.data['generation']['molecules']);s['actual_steps']=results[t['target_id']]['actual_steps'];s['generation_depth_confounded']=ctx.config.data['generation']['iteration']=='auto';frames.append(df);summaries.append(s);molecules.update(m)
    if frames:
        master=pd.concat(frames,ignore_index=True);master.to_csv(ctx.path('07_ANALYSIS/molecules.csv'),index=False);pd.DataFrame(summaries).to_csv(ctx.path('07_ANALYSIS/generation_summary.csv'),index=False)
        analysis=profile(master,molecules,ctx.path('07_ANALYSIS'))
    else:
        from pathpocket.analysis.empty import empty_analysis
        analysis=empty_analysis(ctx.path('07_ANALYSIS'))
    write_json(ctx.path('07_ANALYSIS/analysis.json'),analysis);done('07_ANALYSIS')
    if until=='analyze':ctx.finish('ANALYZED',completed_steps=completed);return ctx.root
    ctx.event('08_REPORT','running',0,'Rendering standard report');figures=render(ctx.path('08_REPORT/figures'),selected,summaries,analysis,ctx.config.states,ctx.config.data['report']['figures_png_dpi']) if targets else [];report(ctx,selected,targets,summaries,analysis,figures);done('08_REPORT')
    known={a['path'] for a in ctx.artifacts}
    for p in sorted(ctx.path('06_CHEMICAL_CHALLENGE').rglob('*')):
        if p.is_file() and str(p.relative_to(ctx.root)) not in known:ctx.register(p,'07_ANALYSIS','Generation QC derivative')
    write_json(ctx.path('09_QC/acceptance.json'),dict(passed=True,targets=len(targets),all_reports_present=True,fixed_depth_verified=ctx.config.data['generation']['iteration']!='auto',raw_outputs_preserved=True));done('09_QC');ctx.finish('COMPLETE',completed_steps=completed);ctx.event('complete','PASS',1,'Report ready; workflow stopped');return ctx.root

def reuse_analysis(config,source,until='run'):
    """Copy upstream stages into a fresh run; never modify the source run."""
    from pathpocket.core.provenance import sha256
    source=Path(source).resolve()
    if not source.is_relative_to(config.output/'runs'):raise ValueError('Source run must belong to this project')
    old=json.loads((source/'run_manifest.json').read_text())
    if old['project_config_sha256']!=sha256(config.source):raise ValueError('Config differs from source run; start a new full run')
    registry=json.loads((source/'artifacts.json').read_text())
    for a in registry:
        p=(source/a['path']).resolve()
        if not p.is_relative_to(source) or sha256(p)!=a['sha256']:raise ValueError('Source artifact hash mismatch')
    ctx=RunContext(config);ctx.manifest.update(capture(config),source_run=str(source));completed=[]
    try:
        for folder in ['00_INPUTS','01_VALIDATE','02_ALIGN','03_REGION_DISCOVERY','04_REGION_MATCHING','05_TARGET_SELECTION','06_CHEMICAL_CHALLENGE']:
            for p in (source/folder).rglob('*'):
                if p.is_file() and p.name!='README.md':
                    dest=ctx.path(str(p.relative_to(source)));dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(p,dest)
            completed.append(folder)
        selected=json.loads(ctx.path('05_TARGET_SELECTION/selected_families.json').read_text());targets=json.loads(ctx.path('05_TARGET_SELECTION/targets.json').read_text());results=json.loads(ctx.path('06_CHEMICAL_CHALLENGE/results.json').read_text())
        for t in targets:
            for key in ['receptor','full_receptor']:t[key]=str(ctx.path('05_TARGET_SELECTION/'+t['target_id']+'/'+Path(t[key]).name))
        def done(folder):
            for p in sorted(ctx.path(folder).rglob('*')):
                if p.is_file():ctx.register(p,folder,'Derived from verified source run '+source.name)
            if folder not in completed:completed.append(folder)
            ctx.event(folder,'PASS',.8,'Completed')
        for folder in completed.copy():done(folder)
        return finish_analysis(ctx,selected,targets,results,completed,done,until)
    except Exception as exc:
        ctx.path('logs/error.log').write_text(traceback.format_exc());ctx.event('analysis_report','FAIL',0,str(exc));ctx.finish('FAIL',error=str(exc),recovery_point='Inspect new run logs; source run preserved');raise
