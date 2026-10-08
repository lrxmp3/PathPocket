"""Adapter to the independently versioned, validated model checkout."""
import configparser,json,subprocess,time,re,os,signal,shutil
from pathlib import Path
import numpy as np
from pathpocket.core.provenance import sha256
from pathpocket.core.run_context import write_json

def build_config(runtime,generation,target,out):
    cfg=configparser.ConfigParser();cfg.read(runtime['template_config']);root=Path(runtime['ed2mol_root'])
    for section in ['lib','model']:
        for key,value in cfg[section].items():cfg[section][key]=str((root/value).resolve())
    for key in ['growth_scope','grow_x','grow_y','grow_z','retain_cores_num','retain_mols_num']:
        cfg.remove_option('sample',key)
    cfg['sample'].update(output_dir=str(Path(out)/'raw'),receptor=str(Path(out)/'receptor.pdb'),reference_core='',iteration='' if generation['iteration']=='auto' else str(generation['iteration']),output_mols_num=str(generation['molecules']),seed=str(generation['seed']),x=str(target['center'][0]),y=str(target['center'][1]),z=str(target['center'][2]))
    for key in ['retain_cores_num','retain_mols_num']:
        if generation.get(key) is not None:cfg['sample'][key]=str(generation[key])
    return cfg

def generate(runtime,generation,target,out):
    out=Path(out);out.mkdir(parents=True,exist_ok=False)
    shutil.copy2(target['receptor'],out/'receptor.pdb');shutil.copy2(target['full_receptor'],out/'receptor_full.pdb')
    cfg=build_config(runtime,generation,target,out)
    with (out/'config.ini').open('w') as f:cfg.write(f)
    start=time.monotonic();command=[runtime['python'],str(Path(runtime['ed2mol_root'])/'tests/run_generation.py'),'--config',str(out/'config.ini')]
    env=os.environ.copy();env['PYTHONDONTWRITEBYTECODE']='1';env['PYTHONPATH']='';env['TMPDIR']=str(out/'tmp');env['XDG_CACHE_HOME']=str(out/'cache');env['CUDA_CACHE_PATH']=str(out/'cache/cuda');env['MPLCONFIGDIR']=str(out/'cache/matplotlib')
    (out/'tmp').mkdir();(out/'cache').mkdir()
    with (out/'generation.log').open('w') as log:
        process=subprocess.Popen(command,cwd=runtime['ed2mol_root'],stdout=log,stderr=subprocess.STDOUT,env=env,start_new_session=True)
        try:code=process.wait(timeout=generation['timeout_seconds'])
        except subprocess.TimeoutExpired:
            os.killpg(process.pid,signal.SIGTERM)
            try:process.wait(timeout=20)
            except subprocess.TimeoutExpired:os.killpg(process.pid,signal.SIGKILL);process.wait()
            code=124
    log=(out/'generation.log').read_text(errors='replace');match=re.search(r'A (\d+)-step Molecule Generation',log)
    result=dict(returncode=code,wall_seconds=time.monotonic()-start,actual_steps=int(match[1]) if match else None,command=command,config_sha256=sha256(out/'config.ini'),caught_tracebacks=log.count('Traceback (most recent call last):'))
    write_json(out/'execution.json',result)
    if code or not (out/'raw/output.sdf').is_file():raise RuntimeError(f'ED2Mol failed: {out}/generation.log')
    if result['caught_tracebacks']:raise RuntimeError(f'ED2Mol caught internal errors; outputs retained for review: {out}')
    if generation['iteration']!='auto' and result['actual_steps']!=generation['iteration']:raise RuntimeError('Fixed generation depth was not respected')
    ed=np.load(out/'raw/ligED.npy')
    if ed.shape!=(48**3,4) or not np.isfinite(ed).all() or not (ed[:,3]>0).any():raise ValueError('Invalid predicted ligand ED')
    result['output_sha256']=sha256(out/'raw/output.sdf');result['ligED_sha256']=sha256(out/'raw/ligED.npy');write_json(out/'execution.json',result)
    return result
