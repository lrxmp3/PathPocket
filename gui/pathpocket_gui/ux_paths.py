"""One path resolver for native Linux and Windows/WSL; no shell string execution."""
import os,sys,json,tempfile,shutil,uuid,subprocess
from pathlib import Path
from .portable_projects import windows_path,wsl_path,infer_workspace

class ProjectPathResolver:
    def __init__(self,distro=None):self.distro=distro or os.environ.get('PATHPOCKET_DISTRO','PathPocket-1-0')
    def native(self,value):return Path(windows_path(value,self.distro) if os.name=='nt' else str(value))
    def backend(self,value):return wsl_path(value,self.distro) if os.name=='nt' else str(Path(value).expanduser().resolve())
    def workspace(self,project):return infer_workspace(self.native(project))
    def project(self,workspace,name):
        from .storage import safe_name
        return Path(workspace).resolve()/'20_PROJECTS'/safe_name(name)
    def run(self,project,run_id):
        if Path(run_id).name!=run_id:raise ValueError('Invalid run ID')
        return Path(project)/'runs'/run_id
    def is_wsl(self):
        if os.name=='nt':return False
        if os.environ.get('WSL_DISTRO_NAME'):return True
        try:return 'microsoft' in Path('/proc/sys/kernel/osrelease').read_text(encoding='utf-8').lower()
        except OSError:return False
    def windows_target(self,path):
        p=Path(path).expanduser().resolve()
        if not self.is_wsl():return str(p)
        try:
            done=subprocess.run(['wslpath','-w',str(p)],capture_output=True,text=True,encoding='utf-8',errors='replace',timeout=10,check=False)
        except (OSError,subprocess.TimeoutExpired) as exc:
            raise OSError('WSL path conversion failed: '+str(p)) from exc
        target=done.stdout.strip()
        if done.returncode or not target:raise OSError('WSL path conversion failed: '+str(p))
        return target
    def _windows_executable(self,name):
        candidates=[Path('/mnt/c/Windows')/name,Path('/mnt/c/Windows/System32')/name]
        for candidate in candidates:
            if candidate.exists():return str(candidate)
        raise OSError('Windows bridge executable is unavailable: '+name)
    def has_default_application(self,path):
        p=Path(path)
        if p.is_dir() or not p.suffix:return True
        if not self.is_wsl():
            if os.name=='nt':return True
            xdg_mime=shutil.which('xdg-mime')
            if not xdg_mime:return False
            try:
                filetype=subprocess.run([xdg_mime,'query','filetype',str(p)],capture_output=True,text=True,encoding='utf-8',errors='replace',timeout=10,check=False)
                mime=filetype.stdout.strip()
                if filetype.returncode or not mime:return False
                default=subprocess.run([xdg_mime,'query','default',mime],capture_output=True,text=True,encoding='utf-8',errors='replace',timeout=10,check=False)
                return default.returncode==0 and bool(default.stdout.strip())
            except (OSError,subprocess.TimeoutExpired):return False
        extension=p.suffix.lower()
        keys=[
            'HKCU\\Software\\Microsoft\\Windows\\CurrentVersion\\Explorer\\FileExts\\'+extension+'\\UserChoice',
            'HKCR\\'+extension,
        ]
        reg=self._windows_executable('reg.exe')
        for key in keys:
            done=subprocess.run([reg,'query',key],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,timeout=10,check=False)
            if done.returncode==0:return True
        return False
    def can_choose_application(self):return self.is_wsl()
    def choose_application(self,path):
        p=Path(path).expanduser().resolve()
        if not p.is_file():raise FileNotFoundError(str(p))
        if not self.is_wsl():return self.open(p)
        target=self.windows_target(p)
        subprocess.Popen([self._windows_executable('rundll32.exe'),'shell32.dll,OpenAs_RunDLL',target],close_fds=True)
        return target
    def _windows_shell_open(self,target,directory=False):
        if directory:
            command=[self._windows_executable('explorer.exe'),target]
        else:
            command=[self._windows_executable('rundll32.exe'),'url.dll,FileProtocolHandler',target]
        try:done=subprocess.run(command,capture_output=True,timeout=15,check=False)
        except (OSError,subprocess.TimeoutExpired) as exc:raise OSError('Windows open request failed: '+target) from exc
        if done.returncode:raise OSError('Windows open request failed with exit code '+str(done.returncode))
    def open(self,path):
        p=Path(path).expanduser().resolve() if self.is_wsl() else self.native(path)
        if not p.exists():raise FileNotFoundError(str(p))
        if self.is_wsl():
            target=self.windows_target(p)
            self._windows_shell_open(target,p.is_dir())
            return target
        from PySide6.QtCore import QUrl
        from PySide6.QtGui import QDesktopServices
        if not QDesktopServices.openUrl(QUrl.fromLocalFile(str(p))):raise OSError('System open request failed: '+str(p))
        return p
    def preflight(self,workspace):
        p=self.native(workspace).expanduser().resolve()
        forbidden=[Path(x) for x in (['C:/Windows','C:/Program Files','C:/Program Files (x86)','D:/CODEX/_ED2MOL','D:/Codex_ED2MOL','E:/calc_data/BSA/ED2Probe_BSA','E:/calc_data/Codex_ED2Mol/01_CODEBASE'] if os.name=='nt' else ['/opt/pathpocket','/bin','/usr','/etc','/sbin'])]
        forbidden+=[Path(os.environ.get('PATHPOCKET_FRONTEND_BUNDLE',Path(__file__).resolve().parents[2]))]
        if os.environ.get('PATHPOCKET_RUNTIME_ROOT'):forbidden.append(self.native(os.environ['PATHPOCKET_RUNTIME_ROOT']))
        if os.name!='nt':forbidden.extend(Path(x) for x in ['/mnt/d/CODEX/_ED2MOL','/mnt/d/Codex_ED2MOL','/mnt/e/calc_data/BSA/ED2Probe_BSA','/mnt/e/calc_data/Codex_ED2Mol/01_CODEBASE'])
        if any(p==x.resolve() or p.is_relative_to(x.resolve()) for x in forbidden):raise ValueError('protected')
        name=None
        try:
            p.mkdir(parents=True,exist_ok=True)
            with tempfile.NamedTemporaryFile(prefix='.pathpocket-write-',dir=p,delete=False) as f:
                name=f.name;f.write(b'PathPocket workspace write probe');f.flush();os.fsync(f.fileno())
        except PermissionError as exc:raise ValueError('unwritable') from exc
        finally:
            if name and Path(name).exists():Path(name).unlink()
        return dict(path=str(p),backend=self.backend(p),writable=True,free_bytes=shutil.disk_usage(p).free)

def preferences_path():
    if os.environ.get('PATHPOCKET_UX_PREFS'):return Path(os.environ['PATHPOCKET_UX_PREFS'])
    base=Path(os.environ.get('LOCALAPPDATA',Path.home())) if os.name=='nt' else Path(os.environ.get('XDG_CONFIG_HOME',Path.home()/'.config'))
    return base/'PathPocket'/'ux-1.0.4.json'
def default_workspace():return Path(os.environ.get('PATHPOCKET_USER_HOME',Path.home()/('Documents' if os.name=='nt' else '')/'PathPocket_Projects'))
def read_preferences():
    defaults=dict(language='system',default_workspace_windows=str(default_workspace()),default_workspace_linux=str(default_workspace()),default_workspace_wsl='',last_project_directory='',use_default=True,remember=True)
    try:defaults.update(json.loads(preferences_path().read_text(encoding='utf-8')))
    except (OSError,ValueError):pass
    return defaults
def save_preferences(data):
    p=preferences_path();p.parent.mkdir(parents=True,exist_ok=True);tmp=p.with_name('.prefs_'+uuid.uuid4().hex+'.tmp');tmp.write_text(json.dumps(data,ensure_ascii=False,indent=2),encoding='utf-8');os.replace(tmp,p)
def preferred_workspace(prefs):
    if prefs.get('remember') and prefs.get('last_project_directory'):return Path(prefs['last_project_directory'])
    return Path(prefs.get('default_workspace_windows' if os.name=='nt' else 'default_workspace_linux') or default_workspace())
