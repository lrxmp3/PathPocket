"""QProcess transport; no scientific imports."""
import json, shutil, uuid, os, sys
from datetime import datetime
from pathlib import Path
from PySide6.QtCore import QObject,QProcess,Signal,QTimer
from .storage import write_json,read_json,guard,to_wsl,validate_settings

COMMANDS={'doctor','init','validate','run','run-engineering-no-targets','status','discover','challenge','analyze','report'}
def diagnostic_text(raw):
    return raw.decode('utf-16-le' if raw.count(b'\x00')>len(raw)//8 else 'utf-8',errors='replace')
class WSLBackendBridge:
    @staticmethod
    def command(settings,request,helper):
        runtime=os.environ['PATHPOCKET_RUNTIME_PYTHON']
        return 'wsl.exe',['-d',settings['distro'],'--exec','/usr/bin/env','PATHPOCKET_WORKSPACE='+to_wsl(settings['root']),'PATHPOCKET_USER_HOME='+to_wsl(settings['root']),runtime,to_wsl(helper),to_wsl(request)]

class NativeLinuxBackendBridge:
    @staticmethod
    def command(settings,request,helper):
        return os.environ['PATHPOCKET_RUNTIME_PYTHON'],[str(helper),str(request)]

def command(settings,request,helper):
    validate_settings(settings)
    transport=WSLBackendBridge if os.name=='nt' else NativeLinuxBackendBridge
    return transport.command(settings,request,helper)

class Bridge(QObject):
    completed=Signal(dict);log=Signal(str);started=Signal(str)
    def __init__(self,settings,parent=None):
        super().__init__(parent);self.settings=settings;self.process=None;self.session=None
    @property
    def busy(self):return self.process is not None and self.process.state()!=QProcess.NotRunning
    def start(self,cmd,args=None,project=None):
        if self.busy:raise RuntimeError('已有后台操作正在运行')
        if cmd not in COMMANDS:raise ValueError('Unsupported CLI command')
        if os.name=='nt' and not shutil.which('wsl.exe'):raise RuntimeError('WSL unavailable：未找到 wsl.exe')
        s=self.settings;validate_settings(s)
        if project:guard(project,Path(s['root'])/'20_PROJECTS')
        session=guard(Path(s['work'])/('GUI_'+datetime.now().strftime('%Y%m%d_%H%M%S')+'_'+uuid.uuid4().hex[:8]),Path(s['root'])/'10_ROUNDS');session.mkdir(parents=True)
        helper=session/'wsl_supervisor.py';shutil.copyfile(Path(__file__).with_name('wsl_supervisor.py'),helper)
        request=dict(workspace=to_wsl(s['root']),command=cmd,arguments=args or [],launcher=s['launcher'],project=to_wsl(project) if project else None,
            fixture_runner=to_wsl(Path(__file__).with_name('engineering_fixture_runner.py')))
        write_json(session/'request.json',request);self.session=session
        exe,argv=command(s,session/'request.json',helper)
        self.process=QProcess(self);self.process.readyReadStandardError.connect(lambda:self.log.emit(diagnostic_text(bytes(self.process.readAllStandardError()))))
        self.process.finished.connect(self._finished);self.process.errorOccurred.connect(self._error)
        self.process.start(exe,argv);self.started.emit(str(session));return session
    def _error(self,error):
        if error==QProcess.FailedToStart:self.completed.emit(dict(status='FAIL',error='WSL unavailable / 无法启动 wsl.exe'))
    def _finished(self,*_):
        try:r=read_json(self.session/'response.json')
        except Exception:r=dict(status='FAIL',error='WSL transport failed; response.json missing. 查看技术日志。')
        r['session']=str(self.session);self.completed.emit(r)
    def stop(self):
        if self.busy:write_json(self.session/'cancel.json',dict(reason='User requested stop'))
