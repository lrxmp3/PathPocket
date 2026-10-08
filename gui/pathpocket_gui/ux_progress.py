"""Read-only projection of structured progress and existing output files."""
import json,datetime,csv,yaml
from pathlib import Path
STAGES=[('initialize','准备运行','Prepare run'),('01_VALIDATE','结构输入检查','Validate structures'),('02_ALIGN','结构对齐','Align structures'),('03_REGION_DISCOVERY','候选区域发现 / 导入','Discover / import regions'),('04_REGION_MATCHING','区域对应关系','Region correspondence'),('05_TARGET_SELECTION','选择挑战目标','Select challenge targets'),('06_CHEMICAL_CHALLENGE','ED2Mol 化学挑战','ED2Mol chemical challenge'),('07_ANALYSIS','质量控制与化学空间','QC and chemical space'),('08_REPORT','生成报告','Build report'),('09_QC','最终检查','Final checks')]
def read(p,default):
 try:return json.loads(Path(p).read_text(encoding='utf-8-sig'))
 except (OSError,ValueError):return default
def snapshot(run,now=None):
 run=Path(run);events=[]
 try:
  for line in (run/'progress.jsonl').read_text(encoding='utf-8-sig').splitlines():
   try:events.append(json.loads(line))
   except ValueError:continue
 except OSError:pass
 last={e.get('step'):e for e in events};manifest=read(run/'run_manifest.json',{});targets=read(run/'05_TARGET_SELECTION/targets.json',[]);done=[];active=[];generated=0;observed=False
 for t in targets:
  folder=run/'06_CHEMICAL_CHALLENGE'/t['target_id'];execution=read(folder/'execution.json',{})
  if execution.get('returncode')==0:done.append(t['target_id'])
  elif folder.exists():active.append(t['target_id'])
  p=folder/'raw/output.sdf'
  if p.exists():generated+=sum(1 for line in p.open(errors='replace') if line.strip()=='$$$$');observed=True
 try:
  start=datetime.datetime.fromisoformat(events[0]['timestamp']);end=datetime.datetime.fromisoformat(events[-1]['timestamp']) if events[-1].get('step')=='complete' else now or datetime.datetime.now(datetime.timezone.utc);elapsed=max(0,int((end-start).total_seconds()))
 except (IndexError,ValueError,KeyError):elapsed=None
 try:requested=yaml.safe_load((run/'00_INPUTS/project.yml').read_text(encoding='utf-8-sig')).get('generation',{}).get('molecules')
 except (OSError,ValueError,AttributeError,yaml.YAMLError):requested=None
 requested=requested*len(targets) if isinstance(requested,int) and targets else None
 complete=manifest.get('status')=='COMPLETE' or 'complete' in last
 return dict(requested=requested,events=events,last=last,targets=targets,done=done,current_target=', '.join(active) or (done[-1] if complete and done else None),generated=generated if observed else None,elapsed=elapsed,complete=complete,stage=events[-1].get('step') if events else 'initialize')
