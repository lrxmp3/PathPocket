"""Deployment UX: hydrate local project copies, validate, and bridge paths."""
import json,os,subprocess,sys
from pathlib import Path
from PySide6.QtCore import QTimer
from PySide6.QtWidgets import QPushButton,QMessageBox,QInputDialog
from .app import Window as ExistingWindow,button
from . import storage
from .portable_projects import infer_workspace,hydrate,unresolved,copy_demo,windows_path,wsl_path,failure_stage

class Window(ExistingWindow):
    def __init__(self,*args,**kwargs):
        self.project_validated=False;self._auto_hydrate=False;self.failure_code=None
        super().__init__(*args,**kwargs)
        self.run_button.setEnabled(False)
        layout=self.pages.widget(0).layout()
        self.demo_button=button('打开示例 / Open Demo',self.open_demo_dialog);layout.insertWidget(2,self.demo_button)
        self.folder_buttons=[b for b in self.findChildren(QPushButton) if b.text()=='打开 Run 文件夹']
        for b in self.folder_buttons:
            b.clicked.disconnect();b.clicked.connect(self.open_run_folder);b.setEnabled(False)
    def adopt_workspace(self,project):
        root=infer_workspace(project)
        from . import app,polish
        storage.ROOT=root;app.ROOT=root;polish.ROOT=root
        os.environ.update(PATHPOCKET_USER_HOME=str(root),PATHPOCKET_WORKSPACE=wsl_path(root))
        self.settings.update(root=str(root),project_parent=str(root/'20_PROJECTS'),work=str(root/'10_ROUNDS'/storage.ROUND/'01_WORK/gui_sessions'))
        self.bridge.settings=self.settings
        for key,widget in self.setting_fields.items():widget.setText(self.settings[key])
    def open_project(self,p):
        self.failure_code=None
        if self.bridge.busy:return self.fail('VALIDATION_FAIL: 请等待当前后台操作完成')
        try:
            p=Path(p);p=p.parent if p.suffix.lower() in ['.yml','.yaml'] else p
            self.adopt_workspace(p);self.project_validated=False;self.run_button.setEnabled(False);self.loaded_run=None;self.last_events=[]
            self.update_folder_buttons();super().open_project(p)
        except Exception as e:self.fail(str(e))
    def populate(self,data):
        self.project_validated=False
        try:
            if unresolved(data):
                yes=self._auto_hydrate
                if not yes:
                    yes=QMessageBox.question(self,'连接本机运行环境','此项目来自便携版模板，需要连接本机 PathPocket 运行环境。是否自动配置？',QMessageBox.Yes|QMessageBox.No,QMessageBox.Yes)==QMessageBox.Yes
                if not yes:
                    super().populate(data);self.yaml_invalid=True;self.run_button.setEnabled(False);self.run_status.setText('RUNTIME_NOT_RESOLVED · 尚未连接本机运行环境');return
            data,audit=hydrate(self.project)
            super().populate(data);self.run_button.setEnabled(False);self.yaml_invalid=True
            self.call('validate',[wsl_path(self.project/'project.yml')],self.project,'open_validate')
        except Exception as e:self.fail(str(e))
        finally:self._auto_hydrate=False
    def open_demo_dialog(self):
        name,ok=QInputDialog.getItem(self,'打开示例','选择示例（创建独立用户副本）',['Conventional HSA','Repeat Aggregate 7KWZ','NO_TARGETS'],0,False)
        if ok:self.open_demo({'Conventional HSA':'DEMO_CONVENTIONAL_HSA','Repeat Aggregate 7KWZ':'DEMO_REPEAT_AGGREGATE_7KWZ','NO_TARGETS':'DEMO_NO_TARGETS'}[name])
    def open_demo(self,name,project_name=None):
        try:
            if self.bridge.busy:raise ValueError('请等待后台操作完成')
            if name not in ['DEMO_CONVENTIONAL_HSA','DEMO_REPEAT_AGGREGATE_7KWZ','DEMO_NO_TARGETS']:raise ValueError('Unknown demo')
            bundle=Path(os.environ['PATHPOCKET_FRONTEND_BUNDLE'])
            dest=copy_demo(bundle/'payload/demos'/name,Path(self.settings['root']),project_name)
            self._auto_hydrate=True;self.open_project(dest);return dest
        except Exception as e:self.fail(str(e))
    def human_error(self,message):
        code=getattr(self,'failure_code',None) or failure_stage(self.task,message,self.last_events,False,bool(self.loaded_run))
        return code+' · '+str(message)[:220]
    def call(self,*args):
        self.failure_code=None
        return super().call(*args)
    def fail(self,message):
        super().fail(message)
        if not self.project_validated:self.run_button.setEnabled(False)
    def on_complete(self,result):
        task=self.task
        if task=='open_validate':
            self.project_validated=result.get('status')=='PASS' and result.get('data',{}).get('passed',True)
            self.yaml_invalid=not self.project_validated;self.run_button.setEnabled(self.project_validated)
            if self.project_validated:
                self.validated_sha256=storage.sha(self.project/'project.yml');self.error_text='';self.run_status.setText('VALIDATION PASS · 本机 workspace/runtime 已连接，可以 Run');self.state_notice.setText('Backend validate PASS');self.page_status[3].setText('✓ VALIDATION PASS')
            else:
                self.failure_code=result.get('failure_stage') or failure_stage(task,result.get('error',''))
                self.fail(result.get('error','VALIDATION_FAIL'))
            self.update_folder_buttons();return
        if result.get('status')=='FAIL':
            events=self.last_events
            if result.get('run_path'):
                from .contracts import progress
                try:events=progress(Path(windows_path(result['run_path'],self.settings['distro']))/'progress.jsonl')
                except (OSError,ValueError):pass
            self.failure_code=result.get('failure_stage') or failure_stage(task,result.get('error',''),events,result.get('ed2mol_started',False),bool(result.get('run_path')))
        else:self.failure_code=None
        super().on_complete(result)
        if task=='save' and result.get('status')=='PASS':self.project_validated=True
        self.update_folder_buttons()
    def run_clicked(self):
        self.failure_code=None
        if not self.project_validated:return self.fail('VALIDATION_FAIL: 请先通过项目校验')
        super().run_clicked()
    def show_poll(self,p):
        super().show_poll(p);self.update_folder_buttons()
    def show_results(self,*args,**kwargs):
        super().show_results(*args,**kwargs);self.update_folder_buttons()
    def update_folder_buttons(self):
        exists=False
        try:exists=bool(self.loaded_run) and Path(windows_path(self.loaded_run,self.settings['distro'])).is_dir()
        except (ValueError,OSError):pass
        for b in getattr(self,'folder_buttons',[]):b.setEnabled(exists)
    def open_run_folder(self):
        actual=self.loaded_run
        try:
            if not actual:raise ValueError('No run has been created')
            if not Path(actual).is_dir():raise FileNotFoundError(str(actual))
            path=self.paths.open(actual)
            self.last_folder_open=dict(original=str(actual),windows_path=str(path),opened=True)
            return True
        except Exception as e:
            self.failure_code='PATH_BRIDGE_FAIL'
            self.fail('打开 run 文件夹失败；实际路径：'+str(actual)+'；'+str(e));return False
