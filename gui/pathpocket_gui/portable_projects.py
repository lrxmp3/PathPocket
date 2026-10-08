"""Portable path/config adaptation only; no scientific parameter changes."""
import copy,datetime,hashlib,json,ntpath,os,re,shutil,uuid
from pathlib import Path
import yaml

RUNTIME_KEYS=('python','ed2mol_root','fpocket','template_config')
ENGINEERING_FIXTURE_FILE='pathpocket_engineering_fixture.json'
NO_TARGETS_FIXTURE_ID='builtin_no_targets_v1'

def _digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def _fixture_inputs(project):
    project=Path(project).resolve()
    return {str(p.relative_to(project)):_digest(p) for p in sorted((project/'inputs').rglob('*')) if p.is_file()}

def _trusted_no_targets_template(template):
    bundle=os.environ.get('PATHPOCKET_FRONTEND_BUNDLE')
    if not bundle:return False
    template=Path(template).resolve();bundle=Path(bundle).resolve()
    return template in {(bundle/'examples/fixtures/DEMO_NO_TARGETS').resolve(),(bundle/'payload/demos/DEMO_NO_TARGETS').resolve()}

def mark_builtin_no_targets_fixture(project):
    """Bind the engineering fixture to this exact GUI-created project copy."""
    project=Path(project).resolve();config=project/'project.yml'
    marker=dict(schema_version=1,fixture_id=NO_TARGETS_FIXTURE_ID,
        semantics='engineering negative control; selected targets forced empty after normal discovery/matching',
        source='bundled:examples/fixtures/DEMO_NO_TARGETS',trusted_builtin=True,
        project_path=str(project),project_name=yaml.safe_load(config.read_text(encoding='utf-8-sig'))['project']['name'],
        project_config_sha256=_digest(config),input_sha256=_fixture_inputs(project))
    atomic(project/ENGINEERING_FIXTURE_FILE,json.dumps(marker,ensure_ascii=False,indent=2))
    return marker

def verified_no_targets_fixture(project):
    """Return audited fixture metadata, or None for ordinary/copied/renamed projects."""
    project=Path(project).resolve();path=project/ENGINEERING_FIXTURE_FILE
    if not path.is_file():return None
    try:
        marker=json.loads(path.read_text(encoding='utf-8'))
        data=yaml.safe_load((project/'project.yml').read_text(encoding='utf-8-sig'))
        checks=[marker.get('schema_version')==1,marker.get('fixture_id')==NO_TARGETS_FIXTURE_ID,
            marker.get('trusted_builtin') is True,marker.get('source')=='bundled:examples/fixtures/DEMO_NO_TARGETS',
            marker.get('project_path')==str(project),marker.get('project_name')==data['project']['name'],
            marker.get('project_config_sha256')==_digest(project/'project.yml'),marker.get('input_sha256')==_fixture_inputs(project)]
        return marker if all(checks) else None
    except (OSError,ValueError,KeyError,TypeError):return None

def windows_path(value,distro=None):
    value=str(value)
    if not value:raise ValueError('Empty path')
    normalized=value.replace('\\','/')
    match=re.match(r'^/mnt/([a-zA-Z])(?:/(.*))?$',normalized)
    if match:return match[1].upper()+':\\'+(match[2] or '').replace('/','\\')
    if normalized.startswith('/') and not normalized.startswith('//'):
        distro=distro or os.environ.get('PATHPOCKET_DISTRO','PathPocket-1-0')
        if not re.fullmatch(r'[A-Za-z0-9_.-]+',distro):raise ValueError('Invalid WSL distribution')
        return '\\\\wsl.localhost\\'+distro+normalized.replace('/','\\')
    return ntpath.normpath(value)

def wsl_path(value,distro=None):
    value=str(value).replace('\\','/')
    match=re.match(r'^([A-Za-z]):/(.*)$',value)
    if match:return '/mnt/'+match[1].lower()+'/'+match[2]
    match=re.match(r'^//wsl(?:\.localhost|\$)/([^/]+)(/.*)?$',value,re.I)
    if match:
        expected=distro or os.environ.get('PATHPOCKET_DISTRO','PathPocket-1-0')
        if match[1].casefold()!=expected.casefold():raise ValueError('WSL distribution mismatch: '+value)
        return match[2] or '/'
    if value.startswith('/') and not value.startswith('//'):return value
    raise ValueError('Absolute Windows/WSL path required: '+value)

def infer_workspace(project):
    project=Path(project).resolve()
    if project.suffix.lower() in ['.yml','.yaml']:project=project.parent
    if project.parent.name!='20_PROJECTS':raise ValueError('WORKSPACE_NOT_AUTHORIZED: project must be directly inside <workspace>/20_PROJECTS')
    return project.parent.parent

def installed_runtime():
    root=os.environ.get('PATHPOCKET_RUNTIME_ROOT')
    if not root:
        launcher=os.environ.get('PATHPOCKET_LAUNCHER','')
        if launcher.endswith('/bin/pathpocket'):root=launcher[:-len('/bin/pathpocket')]
    if not root or not root.startswith('/') or 'SET_BY_FIRST_RUN' in root:raise ValueError('RUNTIME_NOT_RESOLVED: installed runtime root unavailable')
    return dict(python=root+'/runtime/env/bin/python',ed2mol_root=root+'/payload/engine',fpocket=root+'/runtime/fpocket/bin/fpocket',template_config=root+'/payload/engine/template.ini')

def unresolved(data):
    runtime=data.get('runtime',{})
    return any(not runtime.get(k) or 'SET_BY_FIRST_RUN' in str(runtime[k]) for k in RUNTIME_KEYS)

def atomic(path,text):
    path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
    tmp=path.with_name('.hf3_'+uuid.uuid4().hex[:12]+'.tmp')
    try:tmp.write_text(text,encoding='utf-8');os.replace(tmp,path)
    finally:
        if tmp.exists():tmp.unlink()

def hydrate_manifest(project,data):
    value=data.get('region_discovery',{}).get('imported_manifest')
    if not value:return
    manifest=Path(windows_path(value) if os.name=='nt' else value) if str(value).startswith(('/','\\')) or re.match(r'^[A-Za-z]:',str(value)) else project/value
    manifest=manifest.resolve()
    if not manifest.is_relative_to(project):raise ValueError('VALIDATION_FAIL: imported portable manifest must be in the user project copy')
    original=manifest.read_bytes();content=json.loads(original);updated=copy.deepcopy(content);changed=[]
    for target in updated.get('targets',[]):
        for key in ['receptor','full_receptor']:
            path=target.get(key)
            if path and not str(path).startswith(('/','\\')) and not re.match(r'^[A-Za-z]:',str(path)):
                resolved=(manifest.parent/path).resolve()
                if not resolved.is_relative_to(project) or not resolved.is_file():raise ValueError('VALIDATION_FAIL: imported receptor missing/outside project: '+str(resolved))
                target[key]=wsl_path(resolved);changed.append(dict(target=target.get('target_id'),key=key,old=path,new=target[key]))
    if changed:
        history=project/'config_history';history.mkdir(exist_ok=True)
        token=uuid.uuid4().hex[:12];archive=history/('manifest_'+token+'.json')
        with archive.open('xb') as f:f.write(original)
        atomic(manifest,json.dumps(updated,ensure_ascii=False,indent=2))
        atomic(history/('manifest_paths_'+token+'.json'),json.dumps(dict(source=str(manifest),backup=str(archive),source_sha256=hashlib.sha256(original).hexdigest(),changes=changed,scientific_values_unchanged=True),indent=2))

def hydrate(project,runtime=None):
    project=Path(project).resolve();workspace=infer_workspace(project)
    path=project/'project.yml';original=path.read_bytes();data=yaml.safe_load(original.decode('utf-8-sig'));changed=copy.deepcopy(data)
    if unresolved(changed):changed['runtime']=dict(runtime or installed_runtime())
    changed.setdefault('project',{}).setdefault('output_root',wsl_path(project))
    hydrate_manifest(project,changed)
    if changed==data:return data,None
    history=project/'config_history';history.mkdir(exist_ok=True)
    name='pre_hydration_'+datetime.datetime.now().strftime('%Y%m%d_%H%M%S')+'_'+uuid.uuid4().hex[:8]+'.yml'
    archive=history/name
    with archive.open('xb') as f:f.write(original)
    atomic(path,yaml.safe_dump(changed,allow_unicode=True,sort_keys=False))
    audit=dict(workspace=str(workspace),project=str(project),source_sha256=hashlib.sha256(original).hexdigest(),archive=str(archive),hydrated_sha256=hashlib.sha256(path.read_bytes()).hexdigest(),runtime=changed['runtime'],scientific_parameters_changed=False)
    atomic(history/(name+'.json'),json.dumps(audit,ensure_ascii=False,indent=2))
    return changed,audit

def copy_demo(template,workspace,name=None):
    template=Path(template).resolve();workspace=Path(workspace).resolve()
    name=name or template.name+'_'+datetime.datetime.now().strftime('%Y%m%d_%H%M%S')+'_'+uuid.uuid4().hex[:6]
    if not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_-]{0,79}',name):raise ValueError('Invalid project name')
    dest=workspace/'20_PROJECTS'/name
    if dest.exists():raise ValueError('Project exists; refusing overwrite')
    shutil.copytree(template,dest,ignore=shutil.ignore_patterns('runs','__pycache__','config_history'))
    # Preserve template bytes before assigning the new copy's identity.
    data,audit=hydrate(dest)
    data['project'].update(name=name,output_root=wsl_path(dest))
    atomic(dest/'project.yml',yaml.safe_dump(data,allow_unicode=True,sort_keys=False))
    if _trusted_no_targets_template(template):mark_builtin_no_targets_fixture(dest)
    return dest

def failure_stage(task,error,events=(),engine_started=False,run_exists=False):
    text=str(error).lower()
    if 'pathpocket_workspace' in text or 'workspace_not_authorized' in text or 'canonical workspace' in text:return 'WORKSPACE_NOT_AUTHORIZED'
    if 'set_by_first_run' in text or 'runtime path missing' in text or 'runtime_not_resolved' in text:return 'RUNTIME_NOT_RESOLVED'
    if task!='run' or not run_exists:return 'VALIDATION_FAIL'
    steps=[e.get('step','') for e in events if e.get('step')!='GUI_VALIDATE']
    last=steps[-1] if steps else ''
    if last in ['01_VALIDATE','02_ALIGN']:return 'STRUCTURE_QC_FAIL'
    if last in ['03_REGION_DISCOVERY','04_REGION_MATCHING']:return 'REGION_DISCOVERY_FAIL'
    if last=='05_TARGET_SELECTION':return 'TARGET_SELECTION_FAIL'
    if last=='06_CHEMICAL_CHALLENGE':return 'ED2MOL_FAIL' if engine_started else 'CHEMICAL_CHALLENGE_PREFLIGHT_FAIL'
    if last=='07_ANALYSIS':return 'ANALYSIS_QC_FAIL'
    if last in ['08_REPORT','09_QC']:return 'REPORT_QC_FAIL'
    return 'RUN_PREFLIGHT_FAIL'
