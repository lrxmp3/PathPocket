from pathlib import Path
import argparse,os,shutil,subprocess,json
import yaml
p=argparse.ArgumentParser();p.add_argument('--workspace',type=Path,required=True);p.add_argument('--runtime',type=Path,required=True);p.add_argument('--run',action='store_true');a=p.parse_args()
src=Path(__file__).resolve().parents[1]/'examples/HSA_MINIMAL_10';dst=a.workspace.resolve()/'20_PROJECTS/HSA_MINIMAL_10'
if dst.exists():raise SystemExit('Use a new workspace to preserve previous results.')
shutil.copytree(src/'input',dst/'input');cfg=yaml.safe_load((src/'config/project.yml').read_text())
for state in cfg['protein']['states'].values():state['structures']=[s.replace('../input/','input/') for s in state['structures']]
cfg['region_discovery']['imported_manifest']=cfg['region_discovery']['imported_manifest'].replace('../input/','input/')
runtime=a.runtime.resolve();cfg['runtime'].update(python=str(runtime/'runtime/env/bin/python'),ed2mol_root=str(runtime/'payload/engine'),fpocket=str(runtime/'runtime/fpocket/bin/fpocket'),template_config=str(runtime/'payload/engine/template.ini'))
manifest=dst/'input/target_manifest.json';data=json.loads(manifest.read_text())
for target in data['targets']:
 for key in ['receptor','full_receptor']:target[key]=str((manifest.parent/target[key]).resolve())
manifest.write_text(json.dumps(data,indent=2))
yaml.safe_dump(cfg,(dst/'project.yml').open('w'),sort_keys=False)
print('Prepared',dst,'; no generation has been started.')
if a.run:
 if os.name=='nt':raise SystemExit('Run generation inside Linux/WSL or use the installed Windows GUI.')
 env=dict(os.environ,PATHPOCKET_WORKSPACE=str(a.workspace.resolve()))
 subprocess.run([str(runtime/'bin/pathpocket'),'doctor'],check=True,env=env)
 subprocess.run([str(runtime/'bin/pathpocket'),'run',str(dst/'project.yml')],check=True,env=env)
