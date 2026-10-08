import datetime,json,time,shutil
from pathlib import Path
from .paths import guard_write
from .provenance import now,sha256

STEPS=['00_INPUTS','01_VALIDATE','02_ALIGN','03_REGION_DISCOVERY','04_REGION_MATCHING','05_TARGET_SELECTION','06_CHEMICAL_CHALLENGE','07_ANALYSIS','08_REPORT','09_QC','logs']

def write_json(path,data):
    path=Path(path);temporary=path.with_name(path.name+'.writing')
    temporary.write_text(json.dumps(data,indent=2,ensure_ascii=False,allow_nan=False,default=str),encoding='utf-8');temporary.replace(path)

class RunContext:
    def __init__(self,config):
        self.config=config; self.artifacts=[]
        parent=guard_write(config.output/'runs',config.workspace/'20_PROJECTS');parent.mkdir(parents=True,exist_ok=True)
        while True:
            self.root=parent/datetime.datetime.now().strftime('RUN_%Y%m%d_%H%M%S')
            try:self.root.mkdir();break
            except FileExistsError:time.sleep(1.01)
        for step in STEPS:
            (self.root/step).mkdir();(self.root/step/'README.md').write_text(f'# {step}\nIndependent run {self.root.name}. Outputs are retained on failure.\n')
        self.manifest={'status':'RUNNING','run_id':self.root.name,'start_time':now()}
        write_json(self.root/'run_manifest.json',self.manifest);write_json(self.root/'artifacts.json',[])
        self.event('initialize','running',0,'Created new immutable run directory')
    def path(self,value):return guard_write(self.root/value,self.root)
    def event(self,step,status,progress,message):
        with self.path('progress.jsonl').open('a',encoding='utf-8') as f:
            f.write(json.dumps(dict(timestamp=now(),step=step,status=status,progress=progress,message=message),ensure_ascii=False)+'\n')
    def register(self,path,step,description,source_artifacts=()):
        path=guard_write(path,self.root);relative=str(path.relative_to(self.root))
        if any(a['path']==relative for a in self.artifacts):raise ValueError(f'Already registered: {relative}')
        aid='A'+str(len(self.artifacts)+1).zfill(6)
        self.artifacts.append(dict(artifact_id=aid,step=step,type=path.suffix.lstrip('.') or 'file',path=relative,sha256=sha256(path),created_at=now(),source_artifacts=list(source_artifacts),description=description))
        write_json(self.path('artifacts.json'),self.artifacts);return aid
    def snapshot(self,path,name):
        dest=self.path('00_INPUTS/'+name);dest.parent.mkdir(parents=True,exist_ok=True)
        if dest.exists():raise ValueError('Input snapshot already exists')
        before=sha256(path);shutil.copy2(path,dest)
        if before!=sha256(dest):raise RuntimeError('Input hash changed during copy')
        self.register(dest,'inputs',f'Immutable copy of {path}');return dest
    def finish(self,status,**extra):
        if 'platform_source_sha256' in self.manifest:
            from .provenance import platform_source
            end=platform_source()
            self.manifest.update(platform_source_sha256_end=end,platform_code_changed_during_run=end!=self.manifest['platform_source_sha256'])
        self.manifest.update(status=status,end_time=now(),**extra);write_json(self.path('run_manifest.json'),self.manifest)
