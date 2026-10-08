import os,json
from pathlib import Path
import yaml
from .paths import native_path,guard_write

def initialize(path):
    root=native_path(os.environ['PATHPOCKET_WORKSPACE']);path=guard_write(path,root/'20_PROJECTS')
    if path.exists():raise ValueError('Project config already exists; refusing overwrite')
    path.parent.mkdir(parents=True,exist_ok=True);(path.parent/'inputs').mkdir(exist_ok=True)
    runtime=json.loads((root/'00_PROJECT_CONTROL/pathpocket_runtime.json').read_text())
    data=dict(project=dict(name=path.parent.name,profile='fast',output_root=str(path.parent)),protein=dict(states={'reference':dict(label='Reference',order=0,structures=['inputs/reference.pdb']),'perturbed':dict(label='Perturbed',order=1,structures=['inputs/perturbed.pdb'])}),runtime=runtime,generation=dict(iteration=2,molecules=100,seed=42))
    path.write_text(yaml.safe_dump(data,sort_keys=False));(path.parent/'README.md').write_text('# Project\nPlace real input PDB files in inputs/, then validate. Each execution creates a fresh run.\n');return path

def status(project):
    project=native_path(project);runs=sorted((project/'runs').glob('RUN_*/run_manifest.json'))
    if not runs:return dict(status='NO_RUNS',project=str(project))
    p=runs[-1];data=json.loads(p.read_text());data['run_path']=str(p.parent)
    progress=p.parent/'progress.jsonl'
    if progress.exists():
        lines=progress.read_text().splitlines()
        if lines:
            try:data['latest_event']=json.loads(lines[-1])
            except json.JSONDecodeError:data['latest_event']=json.loads(lines[-2]) if len(lines)>1 else None
    return data
