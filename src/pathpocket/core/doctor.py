import os,sys,json,platform,subprocess,shutil
from pathlib import Path
import torch
from .paths import native_path

def doctor(config=None):
    workspace=native_path(os.environ['PATHPOCKET_WORKSPACE']);runtime=config.data['runtime'] if config else json.loads((workspace/'00_PROJECT_CONTROL/pathpocket_runtime.json').read_text())
    root=native_path(runtime['ed2mol_root']);python=native_path(runtime['python']);fp=native_path(runtime['fpocket'])
    code='import sys;sys.path.insert(0,sys.argv[1]);import Generate;print("ED2Mol import OK")'
    env=os.environ.copy();env['PYTHONDONTWRITEBYTECODE']='1';env['PYTHONPATH']=''
    proc=subprocess.run([str(python),'-c',code,str(root)],cwd=root,env=env,capture_output=True,text=True,timeout=180)
    check=subprocess.run([str(fp),'-h'],capture_output=True,text=True,timeout=30)
    free=shutil.disk_usage(workspace).free
    checks=dict(python=sys.version_info>=(3,11),WSL='microsoft' in platform.release().lower(),GPU=torch.cuda.is_available(),PyTorch=bool(torch.__version__),fpocket='fpocket' in check.stdout+check.stderr,ED2Mol_weights=all((root/'weights'/p).is_file() for p in ['GPPM.pth','TAPM.pth','Pocket2ED.pt']),ED2Mol_import=proc.returncode==0,disk_space=free>5*1024**3,canonical_workspace=workspace.is_dir())
    return dict(passed=all(checks.values()),checks=checks,python=sys.version,pytorch=torch.__version__,cuda=torch.version.cuda,gpu=torch.cuda.get_device_name(0) if torch.cuda.is_available() else None,disk_free_GB=free/1e9,import_log=proc.stdout+proc.stderr,runtime=runtime)
