import datetime, hashlib, platform, subprocess, sys, shutil, os, json
from pathlib import Path
from pathpocket import __version__

def now(): return datetime.datetime.now().astimezone().isoformat()
def sha256(path):
    h=hashlib.sha256()
    with Path(path).open('rb') as f:
        for block in iter(lambda:f.read(1024*1024),b''): h.update(block)
    return h.hexdigest()
def git_commit(path):
    return subprocess.check_output(['git','rev-parse','HEAD'],cwd=path,text=True).strip()
def platform_source():
    package=Path(__file__).resolve().parents[1]
    return {str(Path('pathpocket')/p.relative_to(package)):sha256(p) for p in sorted(package.rglob('*.py'))}
def platform_revision():
    package=Path(__file__).resolve().parents[1];build=package/'_build_info.json'
    if build.is_file():return json.loads(build.read_text())['git_commit'],'installed distribution'
    return git_commit(package),subprocess.check_output(['git','status','--porcelain'],cwd=package,text=True).strip()
def capture(config):
    import torch
    engine=Path(config.data['runtime']['ed2mol_root'])
    fp=Path(config.data['runtime']['fpocket'])
    help_result=subprocess.run([str(fp),'-h'],capture_output=True,text=True)
    commit,status=platform_revision()
    return dict(pathpocket_version=__version__,git_commit=commit,
        platform_git_status=status,platform_source_sha256=platform_source(),
        project_config_sha256=sha256(config.source),python=sys.version,python_executable=sys.executable,
        pytorch=torch.__version__,cuda=torch.version.cuda,gpu=torch.cuda.get_device_name(0) if torch.cuda.is_available() else None,
        fpocket_version=help_result.stdout[:4000]+help_result.stderr[:4000],fpocket_sha256=sha256(fp),
        ed2mol_commit=git_commit(engine),ed2mol_weights={str(p):sha256(p) for p in sorted((engine/'weights').glob('*')) if p.is_file()},
        start_time=now(),end_time=None,host_info=dict(hostname=platform.node(),system=platform.platform()),
        random_seeds=[config.data['generation']['seed']],generation_depth_confounded=config.data['generation']['iteration']=='auto')
