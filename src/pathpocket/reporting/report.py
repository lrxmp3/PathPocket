import html,json
from pathlib import Path
from pathpocket.core.run_context import write_json
from pathpocket import __version__

LIMITATIONS=[
 '本结果用于低精度工作流筛选和假设生成，不用于单独证明病理口袋、结合常数、药物滞留或荧光机制。',
 'fpocket region ≠ validated pocket; predicted ligand ED ≠ experimental electron density.',
 'Generated molecule ≠ binder; Q-score ≠ binding affinity; geometry-compatible ≠ binder.',
 'One representative/state is not ensemble thermodynamics; one seed does not exhaust chemical space.',
 'Generated molecules are not biological independent replicates; no p-value analysis.',
 'Basic geometry QC is not a full strain-energy or pose-validation assessment.',
 'Raw engineering isotope labels are retained; these are not a designed isotope-labelled compound series.',
 'Canonical sequence/chain mapping requires unique high-confidence correspondence; renamed homomers and low-confidence mappings fail safely. Canonical IDs are project-local observed-sequence identities.',
]
HEADINGS=['Project','Inputs','QC','Region discovery','Region families','Selected targets','ED2Mol generation','Chemical-space comparison','Key observations','Limitations','Recommended next step','Reproducibility']

def trusted_engineering_fixture(ctx):
    fixture=getattr(ctx,'manifest',{}).get('engineering_fixture')
    required={'fixture_id','source','semantics','marker_sha256','selection_policy'}
    if not isinstance(fixture,dict) or set(fixture)!=required:return None
    if fixture.get('fixture_id')!='builtin_no_targets_v1':return None
    if fixture.get('selection_policy')!='FORCE_EMPTY_AT_TARGET_SELECTION':return None
    if not isinstance(fixture.get('source'),str) or not isinstance(fixture.get('semantics'),str):return None
    if not isinstance(fixture.get('marker_sha256'),str):return None
    return {key:fixture[key] for key in sorted(required)}

def make_summary(ctx,families,targets,summaries,analysis,figures):
    limitations=list(LIMITATIONS);warnings=[]
    if not any(f.get('strict_state_stable_control',False) for f in families):limitations.append('No strict state-stable control; persistent/remodeling comparators must not be called proven stable controls.')
    if ctx.config.data['generation']['iteration']=='auto':limitations.append('generation_depth_confounded = true: automatic depth is explicitly enabled.');warnings.append('generation_depth_confounded')
    if any(x['generated']<x['requested'] for x in summaries):warnings.append('One or more targets did not reach requested count; output is not padded.')
    if any(x['unique']==0 for x in summaries):warnings.append('One or more targets have zero valid unique molecules; chemical comparisons involving those targets are unavailable, not zero-distance evidence.')
    mapping=getattr(ctx,'manifest',{}).get('residue_mapping')
    if mapping:warnings.extend('Residue mapping: '+w for w in mapping.get('warnings',[]))
    summary=dict(schema_version='0.1.0',project=ctx.config.name,run_id=ctx.root.name,status='COMPLETE',result_class='TARGETS_GENERATED' if targets else 'NO_TARGETS',target_count=len(targets),generation_status='COMPLETE' if targets else 'SKIPPED',residue_mapping=mapping,aggregate=getattr(ctx,'manifest',{}).get('aggregate'),states=ctx.config.states,selected_region_families=families,targets=targets,generation_summary=summaries,key_metrics=dict(generated=sum(x['generated'] for x in summaries),valid_unique_within_targets=sum(x['unique'] for x in summaries),physical_compatible_unique=sum(x['physical_compatible'] for x in summaries),generation_depth_confounded=ctx.config.data['generation']['iteration']=='auto',state_comparisons=analysis['comparisons']),figures=figures,warnings=warnings,limitations=limitations,next_step='Review Fast Screening outputs; further work requires separate authorization.')
    fixture=trusted_engineering_fixture(ctx)
    if fixture:summary['engineering_fixture']=fixture
    return summary

def report(ctx,families,targets,summaries,analysis,figures):
    summary=make_summary(ctx,families,targets,summaries,analysis,figures);out=ctx.path('08_REPORT');write_json(out/'summary.json',summary)
    blocks=[f"{ctx.config.name} — PathPocket v{__version__} Fast Screening prototype. Run {ctx.root.name}.",
      json.dumps({s:dict(label=v['label'],structures=len(v['structures']),metadata=v['metadata']) for s,v in ctx.config.states.items()},ensure_ascii=False,indent=2),
      'Input QC and residue-identity alignment recorded in 01_VALIDATE and 02_ALIGN. Generated-molecule QC is in each target folder. Counts refer to target-local identities.',
      'Imported audited region reference' if ctx.config.data['region_discovery']['imported_manifest'] else 'fpocket top-N candidate discovery; ranks are not pathological classifications.',
      json.dumps(families,ensure_ascii=False,indent=2),json.dumps(targets,ensure_ascii=False,indent=2),json.dumps(summaries,ensure_ascii=False,indent=2),
      'ECFP4 radius 2 / 2048 bits; Butina distance 0.4; Bemis–Murcko scaffolds. Joint family PCA. Property median/IQR and raw-unit Wasserstein distances; directional nearest-neighbor Tanimoto. No inferential p-values.',
      json.dumps(summary['key_metrics'],ensure_ascii=False,indent=2),'\n'.join('- '+s for s in summary['limitations']),summary['next_step'],
      'run_manifest.json records engine and platform commits, weight hashes, config hash, environment and seeds. artifacts.json records file hashes and lineage. progress.jsonl is the machine-readable event contract. Raw model outputs are preserved.']
    if summary['residue_mapping']:
        mapping=summary['residue_mapping'];brief={k:mapping.get(k) for k in ['status','mapping_mode','reference_state','mapped_chains','mapped_residue_count','gap_count','warnings']}
        rows=mapping.get('chain_mappings',[])
        for key in ['identity','coverage_ref','coverage_target']:brief['minimum_'+key]=min((r[key] for r in rows if key in r),default=None)
        blocks[2]+='\nResidue Mapping: '+json.dumps(brief,ensure_ascii=False,indent=2)+'\nFull per-chain confidence and correspondence are recorded in the linked mapping tables.'
    if summary.get('aggregate'):
        blocks[2]+='\nStructure adaptation: '+json.dumps(summary['aggregate'],ensure_ascii=False,indent=2)
    if not targets:
        if summary.get('engineering_fixture'):
            message='Run complete — Engineering NO_TARGETS fixture selected zero targets after normal candidate discovery and matching. This is an engineering control and does not establish that the input protein lacks pockets.'
        else:
            message='Run complete — No targets selected. No region family met the current target-selection criteria.'
        blocks[5]=message;blocks[6]='ED2Mol SKIPPED / NOT_APPLICABLE; engine invocations = 0.';blocks[7]='No chemical-space analysis or molecular figures: no targets.';blocks[8]=message
    md=f'# {ctx.config.name}: Fast Screening\n';body=''
    for i,(heading,block) in enumerate(zip(HEADINGS,blocks),1):
        md+=f'\n## {i}. {heading}\n\n'+('```json\n'+block+'\n```' if block.startswith(('{','[')) else block)+'\n'
        body+=f'<section><h2>{i}. {html.escape(heading)}</h2><pre>{html.escape(block)}</pre></section>'
    for f in figures:
        md+=f'\n![{f["name"]}]({f["path"]})\n\n{f["caption"]}\n'
        body+=f'<figure><img src="{html.escape(f["path"],quote=True)}" alt="{html.escape(f["name"],quote=True)}"><figcaption>{html.escape(f["caption"])}</figcaption></figure>'
    if summary['residue_mapping']:
        md+='\n[Chain mapping](../01_VALIDATE/chain_mapping.csv) · [Residue mapping](../01_VALIDATE/residue_mapping.csv)\n'
        body+='<p><a href="../01_VALIDATE/chain_mapping.csv">Chain mapping</a> · <a href="../01_VALIDATE/residue_mapping.csv">Residue mapping</a></p>'
    (out/'report.md').write_text(md,encoding='utf-8');(out/'report.html').write_text('<!doctype html><html lang="en"><meta charset="utf-8"><title>'+html.escape(ctx.config.name)+' — PathPocket</title><style>body{max-width:1100px;margin:2em auto;font:16px system-ui;line-height:1.5;padding:1em}pre{white-space:pre-wrap;overflow-wrap:anywhere;background:#f5f7f9;padding:1em}img{max-width:100%}section{margin-top:2em}</style><h1>'+html.escape(ctx.config.name)+' — Fast Screening</h1>'+body+'</html>',encoding='utf-8')
    return summary
