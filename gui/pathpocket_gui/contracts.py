"""Read-only output contracts. No molecule processing or scientific ranking."""
import csv,json
from pathlib import Path
from .storage import read_json,inside,sha

def artifact_path(run,value):
    p=Path(run)/value
    if Path(value).is_absolute() or not inside(p,run):raise ValueError('Artifact path escapes run')
    return p

def progress(path):
    if not Path(path).exists():return []
    raw=Path(path).read_bytes();lines=raw.split(b'\n');events=[]
    # Last partial line is pending, not a parse failure.
    for line in lines[:-1]:
        if not line.strip():continue
        d=json.loads(line)
        if not all(k in d for k in ['timestamp','step','status','progress','message']):raise ValueError('Invalid progress contract')
        events.append(d)
    return events

def history(project,session_root=None):
    rows=[]
    for p in sorted((Path(project)/'runs').glob('RUN_*'),reverse=True):
        try:
            m=read_json(p/'run_manifest.json');a=read_json(p/'artifacts.json') if (p/'artifacts.json').exists() else []
            reports=[str(artifact_path(p,x['path'])) for x in a if x.get('type')=='html']
            rows.append(dict(path=str(p),run_id=p.name,date=m.get('start_time',''),status=m.get('status','UNKNOWN'),config_hash=m.get('project_config_sha256',''),report=reports[0] if reports else ''))
            if m.get('aggregate',{}).get('structure_mode')=='unsupported_aggregate':rows[-1].update(status='STOPPED · Unsupported aggregate',backend_status=m.get('status'))
        except Exception as e:rows.append(dict(path=str(p),run_id=p.name,date='',status='UNREADABLE',config_hash='',report='',error=str(e)))
    if session_root:
        interrupted={}
        from .storage import to_windows
        for f in Path(session_root).glob('GUI_*/response.json'):
            try:
                r=read_json(f)
                if r.get('status')=='INTERRUPTED' and r.get('run_path'):interrupted[str(Path(to_windows(r['run_path'])).resolve())]=str(f)
            except (ValueError,OSError):continue
        for row in rows:
            key=str(Path(row['path']).resolve())
            if key in interrupted:row.update(backend_status=row['status'],status='INTERRUPTED (GUI)',gui_record=interrupted[key])
    return rows

def load_run(run):
    run=Path(run);m=read_json(run/'run_manifest.json');a=read_json(run/'artifacts.json')
    if not isinstance(a,list):raise ValueError('artifacts.json must be a list')
    index={};warnings=[]
    for x in a:
        if not all(k in x for k in ['artifact_id','path','type','sha256']):raise ValueError('Invalid artifact contract')
        p=artifact_path(run,x['path']);index[x['path']]=x
        if not p.is_file():warnings.append('Artifact missing: '+x['path'])
    aggregate_tables={}
    for x in a:
        name=Path(x['path']).name
        if name in ['aggregate_qc.json','repeat_chain_table.csv']:aggregate_tables.setdefault(name,str(artifact_path(run,x['path'])))
    aggregate=m.get('aggregate')
    if aggregate and aggregate.get('structure_mode')=='unsupported_aggregate':
        return dict(run=str(run),manifest=m,summary=None,artifacts=a,aggregate=aggregate,aggregate_tables=aggregate_tables,run_kind='structure_adaptation_stopped',status='STOPPED',warnings=[aggregate['status']],figures=[],reports={},diversity={})
    # Summary is a documented contract file; report and images are discovered by artifact type.
    candidates=[artifact_path(run,x['path']) for x in a if x['type']=='json' and Path(x['path']).name=='summary.json']
    if len(candidates)!=1:raise ValueError('summary missing / ambiguous; 不能显示 PASS')
    sp=candidates[0];s=read_json(sp)
    for key in ['project','run_id','status','states','selected_region_families','targets','generation_summary','key_metrics','figures','warnings','limitations']:
        if key not in s:raise ValueError('Summary contract missing: '+key)
    if s['run_id']!=m['run_id'] or s['run_id']!=run.name:raise ValueError('Run identity mismatch')
    figures=[]
    for x in a:
        if x['type'] not in ['png','jpg','jpeg']:continue
        p=artifact_path(run,x['path']);related={}
        for ext in ['csv','svg','pdf']:
            rel=str(Path(x['path']).with_suffix('.'+ext)).replace('\\','/')
            if rel in index:related[ext]=str(artifact_path(run,rel))
        figures.append(dict(path=str(p),name=p.stem,related=related,missing=not p.exists()))
    order={str((sp.parent/f['path']).resolve()):i for i,f in enumerate(s['figures']) if isinstance(f,dict) and 'path' in f}
    figures.sort(key=lambda f:order.get(str(Path(f['path']).resolve()),len(order)))
    reports={}
    for x in a:
        if x['type']=='html':reports['html']=str(artifact_path(run,x['path']))
        if x['type'] in ['md','markdown'] and Path(x['path']).name=='report.md':reports['md']=str(artifact_path(run,x['path']))
    # Read exported diversity rows by columns, never recompute molecular metrics.
    diversity={}
    for x in a:
        if x['type']!='csv' or x.get('step')!='07_ANALYSIS':continue
        p=artifact_path(run,x['path'])
        if not p.is_file():continue
        with p.open(encoding='utf-8-sig',newline='') as f:
            reader=csv.DictReader(f);fields=set(reader.fieldnames or [])
            if {'state_id','region_family_id'}.issubset(fields) and any('diversity' in k for k in fields):
                for row in reader:diversity[(row['region_family_id'],row['state_id'])]=row
    if m.get('status')!='COMPLETE' or s.get('status')!='COMPLETE':warnings.append('Run incomplete: '+str(m.get('status')))
    if not reports.get('html'):warnings.append('HTML report missing')
    aggregate=s.get('aggregate',aggregate)
    if aggregate:
        for record in [aggregate]+aggregate.get('adapters',[]):
            for warning in record.get('warnings',[]):
                if warning not in warnings:warnings.append(warning)
    mapping=s.get('residue_mapping')
    mapping_tables={Path(x['path']).name:str(artifact_path(run,x['path'])) for x in a if Path(x['path']).name in ['chain_mapping.csv','residue_mapping.csv']}
    return dict(run=str(run),manifest=m,summary=s,artifacts=a,figures=figures,reports=reports,diversity=diversity,mapping=mapping,mapping_tables=mapping_tables,aggregate=s.get('aggregate',aggregate),aggregate_tables=aggregate_tables,warnings=warnings,status='WARN' if warnings else 'COMPLETE')

def poll_session(session):
    session=Path(session);state=read_json(session/'state.json') if (session/'state.json').exists() else {}
    from .storage import to_windows
    run=Path(to_windows(state['run_path'])) if state.get('run_path') else None
    return dict(state=state,run=str(run) if run else None,events=progress(run/'progress.jsonl') if run else [],
        logs='\n'.join((session/n).read_text(encoding='utf-8',errors='replace')[-12000:] for n in ['stdout.log','stderr.log'] if (session/n).exists()))
