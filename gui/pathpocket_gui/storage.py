"""Presentation-side storage only. Scientific validation belongs to backend."""
import hashlib, json, os, re, shutil, uuid
from pathlib import Path
import yaml

ROOT = Path(os.environ.get('PATHPOCKET_USER_HOME', str(Path.home()/'PathPocket_Projects'))).resolve()
ROUND = 'R001_PORTABLE_SESSIONS'
LEGACY = []


def to_windows(value):
    if os.name!='nt':return to_wsl(value)
    from .portable_projects import windows_path
    return windows_path(value)

def to_wsl(value):
    from .portable_projects import wsl_path
    return wsl_path(value)


def safe_name(value):
    if not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_-]{0,79}', value or '') or value.upper() in {'CON','PRN','AUX','NUL',*[f'COM{i}' for i in range(1,10)],*[f'LPT{i}' for i in range(1,10)]}:
        raise ValueError('名称只能包含字母、数字、下划线或连字符，不能使用保留名称')
    return value

def inside(path, parent):
    return Path(path).resolve().is_relative_to(Path(parent).resolve())

def guard(path, parent):
    path = Path(to_windows(path)).resolve()
    if any(inside(path, p) for p in LEGACY) or not inside(path, parent):
        raise ValueError('禁止写入 LEGACY 或指定项目范围之外的路径')
    return path

def atomic_text(path, text):
    path = Path(path); path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(path.name+'.'+uuid.uuid4().hex+'.tmp')
    try:
        tmp.write_text(text, encoding='utf-8', newline='\n'); os.replace(tmp,path)
    finally:
        if tmp.exists(): tmp.unlink()

def write_json(path, data): atomic_text(path,json.dumps(data,ensure_ascii=False,indent=2))
def read_json(path): return json.loads(Path(path).read_text(encoding='utf-8-sig'))
def sha(path):
    h=hashlib.sha256()
    with open(path,'rb') as f:
        for b in iter(lambda:f.read(1024*1024), b''):h.update(b)
    return h.hexdigest()

class StrictLoader(yaml.SafeLoader): pass
def mapping(loader,node,deep=False):
    result={}
    for k,v in node.value:
        key=loader.construct_object(k,deep=deep)
        if key in result: raise ValueError('YAML 重复键: '+str(key))
        result[key]=loader.construct_object(v,deep=deep)
    return result
StrictLoader.add_constructor(yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG,mapping)
def parse_yaml(text):
    data=yaml.load(text,Loader=StrictLoader)
    if not isinstance(data,dict):raise ValueError('YAML 必须是 mapping')
    return data
def dump_yaml(data):return yaml.safe_dump(data,allow_unicode=True,sort_keys=False)

def default_settings():
    return dict(root=str(ROOT), distro=os.environ.get('PATHPOCKET_DISTRO','PathPocket-1-0'), launcher=os.environ['PATHPOCKET_LAUNCHER'],
        project_parent=str(ROOT/'20_PROJECTS'),work=str(ROOT/'10_ROUNDS'/ROUND/'01_WORK/gui_sessions'),
        open_report=False,theme='System',recent=[],remember_project=False)
def settings_file():
    explicit=os.environ.get('PATHPOCKET_GUI_SETTINGS')
    if explicit:return guard(explicit,ROOT/'10_ROUNDS'/ROUND)
    return ROOT/'00_PROJECT_CONTROL'/'gui-settings-portable-v1.0.json'
def load_settings():
    d=default_settings()
    source=settings_file()
    if not source.exists():source=source.with_name('gui-settings.json')
    if source.exists():d.update(read_json(source))
    d.update({k:default_settings()[k] for k in ['root','distro','launcher','project_parent','work']})
    return d
def save_settings(d):
    validate_settings(d);write_json(settings_file(),d)
def validate_settings(d):
    if not Path(d['root']).is_dir():raise ValueError('用户项目目录不存在')
    guard(d['project_parent'],Path(d['root'])/'20_PROJECTS')
    guard(d['work'],Path(d['root'])/'10_ROUNDS'/ROUND/'01_WORK')
    if not d['distro'] or '\n' in d['distro']:raise ValueError('WSL distribution 无效')
    if not d['launcher'].startswith('/'):raise ValueError('Backend command 必须为 WSL 绝对 launcher 路径')
    if d['theme'] not in ['System','Light','Dark']:raise ValueError('主题无效')

def lightweight_validate(data,project):
    states=data.get('protein',{}).get('states',{})
    if not states:raise ValueError('至少需要一个 Protein State')
    orders=set()
    for sid,s in states.items():
        safe_name(sid)
        if s.get('order') in orders:raise ValueError('State order 冲突')
        orders.add(s.get('order'))
        if not s.get('structures'):raise ValueError(sid+': empty state，请添加 PDB')
        seen=set()
        for p in s['structures']:
            p=Path(to_windows(p));p=p if p.is_absolute() else Path(project)/p
            if not p.is_file():raise ValueError('PDB missing: '+str(p))
            if p.suffix.lower()!='.pdb':raise ValueError('v0.1 仅支持 PDB 输入')
            key=str(p.resolve()).lower()
            if key in seen:raise ValueError('同一 state 中出现重复 PDB')
            seen.add(key)
    return True

def import_structures(files,project,copy=True):
    project=Path(project);folder=guard(project/'inputs',project);folder.mkdir(exist_ok=True)
    records=[];outputs=[]
    for f in files:
        src=Path(f).resolve()
        if not src.is_file() or src.suffix.lower()!='.pdb':raise ValueError('PDB missing / 不支持的输入: '+str(src))
        digest=sha(src)
        if copy:
            dst=guard(folder/(digest[:16]+'_'+src.name),project)
            if dst.exists() and sha(dst)!=digest:raise ValueError('Input hash conflict')
            if not dst.exists():shutil.copy2(src,dst)
            if sha(dst)!=digest:raise ValueError('Copy hash verification failed')
        else:dst=src
        outputs.append(to_wsl(dst));records.append(dict(source=str(src),destination=str(dst),sha256=digest,mode='copy' if copy else 'external_reference'))
    ledger=project/'input_provenance.json';old=read_json(ledger) if ledger.exists() else []
    write_json(ledger,old+records)
    return outputs
