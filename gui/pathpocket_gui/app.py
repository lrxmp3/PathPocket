"""Native Qt front end. All scientific work is delegated to the WSL CLI."""
import copy,json,os,shutil,subprocess,sys,time,uuid
from pathlib import Path
from PySide6.QtCore import Qt,QTimer,QUrl,QSize
from PySide6.QtGui import QDesktopServices,QPixmap,QImageReader,QIcon,QPalette,QColor
from PySide6.QtWidgets import (QApplication,QMainWindow,QWidget,QVBoxLayout,QHBoxLayout,QFormLayout,QLabel,QLineEdit,QPushButton,QListWidget,QStackedWidget,QTableWidget,QTableWidgetItem,QHeaderView,QAbstractItemView,QSpinBox,QDoubleSpinBox,QCheckBox,QComboBox,QGroupBox,QPlainTextEdit,QProgressBar,QFileDialog,QMessageBox,QTabWidget,QScrollArea,QGridLayout,QInputDialog,QDialog,QDialogButtonBox)
from .storage import *
from .bridge import Bridge
from .contracts import load_run,history,poll_session
from .workers import background
from . import __version__

STEPS=[('GUI_VALIDATE','Validate (CLI preflight)'),('01_VALIDATE','Structure QC'),('02_ALIGN','Alignment'),('03_REGION_DISCOVERY','Region Discovery'),('04_REGION_MATCHING','Region Matching'),('05_TARGET_SELECTION','Target Selection'),('06_CHEMICAL_CHALLENGE','ED2Mol Challenge'),('07_ANALYSIS','Analysis / Generation QC'),('08_REPORT','Report'),('09_QC','Output QC')]

def button(text,fn):
    b=QPushButton(text);b.clicked.connect(fn);return b
def label(text):
    w=QLabel(text);w.setWordWrap(True);w.setTextInteractionFlags(Qt.TextSelectableByMouse);return w
def table(headers):
    t=QTableWidget(0,len(headers));t.setHorizontalHeaderLabels(headers);t.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents);t.horizontalHeader().setStretchLastSection(True);t.setSelectionBehavior(QAbstractItemView.SelectRows);return t
def fill(t,rows):
    t.setRowCount(len(rows))
    for i,row in enumerate(rows):
        for j,v in enumerate(row):t.setItem(i,j,QTableWidgetItem('NA' if v is None else str(v)))
def pretty(v):return 'NA' if v is None or v=='' else (f'{v:.4g}' if isinstance(v,float) else str(v))

class Window(QMainWindow):
    def __init__(self,settings=None):
        super().__init__();self.settings=settings or load_settings();self.project=None;self.data=None;self.result=None;self.loaded_run=None;self.task='';self.after=None;self.polling=False;self.session=None;self.error_text='';self.pending_create=None;self.active_run=False;self.started_at=None;self.last_events=[];self.auto_confirmed=False;self.workers=[];self.yaml_invalid=False
        self.setWindowTitle('PathPocket GUI v0.1.0 — Fast Screening');self.resize(1200,800);self.setMinimumSize(980,650)
        outer=QWidget();self.setCentralWidget(outer);layout=QVBoxLayout(outer)
        title=label('PathPocket  /  Fast Screening');title.setStyleSheet('font-size:22px;font-weight:600;color:#26758a');layout.addWidget(title)
        layout.addWidget(label('低精度筛选与假设生成 · Portable GUI → frozen backend · 原始 run 保留'))
        body=QHBoxLayout();layout.addLayout(body,1);self.nav=QListWidget();self.nav.addItems(['1  项目 Project','2  蛋白状态','3  Fast 参数','4  运行 Run','5  结果 Results','设置 / About']);self.nav.setFixedWidth(175);body.addWidget(self.nav);self.pages=QStackedWidget();body.addWidget(self.pages,1);self.nav.currentRowChanged.connect(self.pages.setCurrentIndex)
        self.build_project();self.build_states();self.build_fast();self.build_run();self.build_results();self.build_settings();self.nav.setCurrentRow(0)
        self.bridge=Bridge(self.settings,self);self.bridge.completed.connect(self.on_complete);self.bridge.log.connect(self.log.appendPlainText)
        self.timer=QTimer(self);self.timer.setInterval(1000);self.timer.timeout.connect(self.tick);self.timer.start()
        self.statusBar().showMessage('启动检查中…');self.apply_theme();QTimer.singleShot(150,self.discover)
    def page(self):
        w=QWidget();v=QVBoxLayout(w);self.pages.addWidget(w);return v
    def worker(self,fn,done):self.workers.append(background(fn,done,self.fail))
    def fail(self,message):
        self.error_text=message;self.run_status.setText('FAIL / '+self.human_error(message));self.log.appendPlainText(message);self.statusBar().showMessage('操作失败：'+self.human_error(message))
        if not self.bridge.busy:self.active_run=False;self.run_button.setEnabled(not self.yaml_invalid);self.stop_button.setEnabled(False);self.lock_editors(False)
        if self.task!='run' and not self.active_run:
            self.bar.setValue(0);self.current.setText('本次操作失败；没有启动新的科学 run。历史结果保持不变。')
    def lock_editors(self,locked):
        for index in [0,1,2,5]:self.pages.widget(index).setEnabled(not locked)
    def compact_states(self):
        for i in range(self.states.rowCount()):
            self.states.setRowHeight(i,88)
            for c in [3,4]:
                item=self.states.item(i,c)
                if item:item.setToolTip(item.text())
    def human_error(self,message):
        text=message.lower()
        for word,hint in [('pdb missing','PDB 文件缺失，请重新选择输入。'),('receptor file','PDB 文件缺失，请重新选择输入。'),('yaml','配置无效，请检查 YAML。'),('no space','磁盘空间不足。'),('doctor','Backend doctor 未通过，请查看检查明细。'),('fpocket','fpocket 阶段失败，请查看当前 run 日志。'),('ed2mol','ED2Mol 阶段失败，请查看当前 run 日志。'),('summary','结果摘要缺失或不完整，不能显示成功。'),('wsl','WSL/backend 无法调用，请检查设置。')]:
            if word in text:return hint
        if 'no such file' in text or 'filenotfounderror' in text:return 'Backend 启动器或输入文件不存在，请检查设置与路径。'
        if 'traceback' in text:return '后台操作失败。请展开 Technical details 查看原因；原始输出已保留。'
        return message[:220]
    def build_project(self):
        v=self.page();f=QFormLayout();self.name=QLineEdit();self.path_label=label('尚未打开项目');self.description=QLineEdit();f.addRow('项目名称',self.name);f.addRow('项目目录',self.path_label);f.addRow('说明（GUI 项目元数据）',self.description);v.addLayout(f)
        row=QHBoxLayout();row.addWidget(button('新建项目',self.new_dialog));row.addWidget(button('打开项目',self.open_dialog));row.addWidget(button('复制为新项目',self.clone_dialog));v.addLayout(row)
        v.addWidget(label('最近项目'));self.recent=QListWidget();self.recent.addItems(self.settings.get('recent',[]));self.recent.itemDoubleClicked.connect(lambda i:self.open_project(Path(i.text())));v.addWidget(self.recent)
        v.addWidget(label('Run history · 旧 run 只读，双击查看结果'));self.history_table=table(['Run ID','时间','状态','Config hash','报告']);self.history_table.setEditTriggers(QAbstractItemView.NoEditTriggers);self.history_table.cellDoubleClicked.connect(lambda r,c:self.load_results(self.history_rows[r]['path']));v.addWidget(self.history_table,2);v.addWidget(button('刷新历史',self.refresh_history))
    def new_dialog(self):
        name,ok=QInputDialog.getText(self,'新建项目','项目名称（字母/数字/下划线/连字符）')
        if ok:self.create_project(name)
    def create_project(self,name,clone=None):
        try:
            if self.bridge.busy:raise ValueError('请等待当前操作完成')
            safe_name(name);p=guard(Path(self.settings['project_parent'])/name,Path(self.settings['root'])/'20_PROJECTS')
            if p.exists():raise ValueError('项目目录已经存在，不覆盖；请使用新名称')
            self.pending_create=(p,clone);self.call('init',[to_wsl(p/'project.yml')],None,'init')
        except Exception as e:self.fail(str(e))
    def clone_dialog(self):
        if not self.project:return self.fail('请先打开要复制的项目')
        name,ok=QInputDialog.getText(self,'复制项目','新项目名称（只复制配置和 inputs，不复制历史 run）')
        if ok:self.create_project(name,self.project)
    def open_dialog(self):
        p,_=QFileDialog.getOpenFileName(self,'打开 project.yml',self.settings['project_parent'],'YAML (*.yml *.yaml)')
        if p:self.open_project(Path(p).parent)
    def open_project(self,p):
        try:
            if self.bridge.busy:raise ValueError('运行期间不能切换项目')
            p=guard(p,Path(self.settings['root'])/'20_PROJECTS');self.project=p
            self.worker(lambda:parse_yaml((p/'project.yml').read_text(encoding='utf-8-sig')),self.populate)
        except Exception as e:self.fail(str(e))
    def populate(self,d):
        self.data=d;self.yaml_invalid=False;self.run_button.setEnabled(True);self.name.setText(d['project']['name']);self.path_label.setText(str(self.project));self.description.setText(read_json(self.project/'gui_project.json').get('description','') if (self.project/'gui_project.json').exists() else '')
        states=d['protein']['states'];fill(self.states,[[sid,s.get('label',sid),s.get('order',i),'\n'.join(to_windows(p) for p in s.get('structures',[])),json.dumps(s.get('metadata',{}),ensure_ascii=False)] for i,(sid,s) in enumerate(states.items())]);self.compact_states()
        g=d.get('generation',{});self.molecules.setValue(g.get('molecules',100));self.seed.setValue(g.get('seed',42));depth=g.get('iteration',2);self.depth.setCurrentText('Auto' if depth=='auto' else str(depth));self.auto_confirmed=False
        disc=d.get('region_discovery',{});self.top_n.setValue(disc.get('top_n',10));sel=d.get('target_selection',{});self.families.setValue(sel.get('max_region_families',3));self.comparator.setChecked(sel.get('include_comparator',True));m=d.get('region_matching',{});self.centroid.setValue(m.get('centroid_cutoff_A',6));self.jaccard.setValue(m.get('residue_jaccard_min',.3));self.sensitivity.setChecked(m.get('sensitivity_analysis',False));self.import_note.setText('导入已审计 region manifest：'+str(disc['imported_manifest']) if disc.get('imported_manifest') else '区域来源：本次调用 fpocket 自动发现')
        self.sync_preset()
        recent=[str(self.project)]+[x for x in self.settings.get('recent',[]) if x!=str(self.project)];self.settings['recent']=recent[:12];save_settings(self.settings);self.update_recent();self.refresh_history();self.statusBar().showMessage('项目已加载；保存时由 backend 校验')
    def update_recent(self):self.recent.clear();self.recent.addItems(self.settings.get('recent',[]))
    def clone_inputs(self,p,source):
        d=parse_yaml((source/'project.yml').read_text(encoding='utf-8'));records=[]
        for src in (source/'inputs').rglob('*'):
            if src.is_file():
                dst=guard(p/'inputs'/src.relative_to(source/'inputs'),p);dst.parent.mkdir(parents=True,exist_ok=True);before=sha(src);shutil.copy2(src,dst)
                if sha(dst)!=before:raise ValueError('Clone hash mismatch')
                records.append(dict(source=str(src),destination=str(dst),sha256=before))
        old=to_wsl(source);new=to_wsl(p)
        def remap(x):
            if isinstance(x,str):return new+x[len(old):] if x==old or x.startswith(old+'/') else x
            if isinstance(x,list):return [remap(v) for v in x]
            if isinstance(x,dict):return {k:remap(v) for k,v in x.items()}
            return x
        # Imported reference paths are metadata; only rewrite copied reference JSON paths.
        for f in (p/'inputs').rglob('*.json'):write_json(f,remap(read_json(f)))
        d=remap(d);d['project']['name']=p.name;d['project']['output_root']=new
        for rec in records:rec['destination_sha256']=sha(rec['destination'])
        write_json(p/'input_provenance.json',records);atomic_text(p/'project.yml',dump_yaml(d));return d
    def refresh_history(self):
        if self.project:
            project=self.project
            self.worker(lambda:history(project,self.settings['work']),lambda rows:self.show_history(rows) if self.project==project else None)
    def show_history(self,rows):
        self.history_rows=rows;fill(self.history_table,[[r['run_id'],r['date'],r['status'],r['config_hash'][:12],bool(r['report'])] for r in rows])
    def build_states(self):
        v=self.page();v.addWidget(label('每行一个状态；Structure(s) 为每行一个绝对路径。Metadata 为 JSON。真正结构 QC 由 backend 执行。'))
        self.states=table(['State ID','Label','Order','Structure(s)','Metadata']);self.states.horizontalHeader().setStretchLastSection(False);self.states.horizontalHeader().setSectionResizeMode(3,QHeaderView.Stretch);self.states.horizontalHeader().setSectionResizeMode(4,QHeaderView.Fixed);self.states.setColumnWidth(4,180);self.states.setWordWrap(False);self.states.cellDoubleClicked.connect(self.edit_state_cell);v.addWidget(self.states,1)
        row=QHBoxLayout()
        for name,fn in [('添加状态',self.add_state),('移除状态',self.remove_state),('上移',lambda:self.move_state(-1)),('下移',lambda:self.move_state(1)),('添加 PDB（可多选）',self.browse_pdb)]:row.addWidget(button(name,fn))
        v.addLayout(row);self.copy_input=QCheckBox('复制到项目 inputs 并记录 SHA256（推荐）');self.copy_input.setChecked(True);v.addWidget(self.copy_input);v.addWidget(button('轻量检查 + Backend 校验并保存',self.save_config));self.state_notice=label('');v.addWidget(self.state_notice)
        self.input_timer=QTimer(self);self.input_timer.setSingleShot(True);self.input_timer.setInterval(500);self.input_timer.timeout.connect(self.check_inputs);self.states.itemChanged.connect(lambda:self.input_timer.start())
    def check_inputs(self):
        if not self.data:return
        try:
            d=self.collect();p=self.project
            self.workers.append(background(lambda:lightweight_validate(d,p),lambda _:self.state_notice.setText('输入轻量检查 PASS；保存仍需 backend validate'),lambda msg:self.state_notice.setText('WARN · '+msg)))
        except Exception as e:self.state_notice.setText('WARN · '+str(e))
    def edit_state_cell(self,r,c):
        if c not in [3,4]:return
        dialog=QDialog(self);dialog.setWindowTitle('编辑 Structure paths / Metadata');dialog.resize(820,460);v=QVBoxLayout(dialog);editor=QPlainTextEdit(self.states.item(r,c).text());v.addWidget(editor);buttons=QDialogButtonBox(QDialogButtonBox.Save|QDialogButtonBox.Cancel);v.addWidget(buttons);buttons.accepted.connect(dialog.accept);buttons.rejected.connect(dialog.reject)
        if dialog.exec()==QDialog.Accepted:self.states.setItem(r,c,QTableWidgetItem(editor.toPlainText()));self.compact_states()
    def add_state(self):
        n=self.states.rowCount();self.states.insertRow(n)
        used={self.states.item(i,0).text() for i in range(n) if self.states.item(i,0)};k=n+1
        while 'state_'+str(k) in used:k+=1
        for j,x in enumerate(['state_'+str(k),'State '+str(k),str(n),'','{}']):self.states.setItem(n,j,QTableWidgetItem(x))
        self.states.selectRow(n)
    def remove_state(self):
        r=self.states.currentRow()
        if r>=0:self.states.removeRow(r);self.reorder()
    def reorder(self):
        for i in range(self.states.rowCount()):self.states.setItem(i,2,QTableWidgetItem(str(i)))
    def move_state(self,delta):
        r=self.states.currentRow();n=r+delta
        if r<0 or n<0 or n>=self.states.rowCount():return
        for c in range(5):
            a=self.states.takeItem(r,c);b=self.states.takeItem(n,c);self.states.setItem(r,c,b);self.states.setItem(n,c,a)
        self.reorder();self.states.selectRow(n)
    def browse_pdb(self):
        if not self.project:return self.fail('先新建或打开项目')
        r=self.states.currentRow()
        if r<0:return self.fail('请先选择一个 state')
        files,_=QFileDialog.getOpenFileNames(self,'添加 PDB',str(self.project),'Protein (*.pdb)')
        if files:self.add_pdbs(r,files,self.copy_input.isChecked())
    def add_pdbs(self,r,files,copy_files=True):
        project=self.project;sid=self.states.item(r,0).text()
        if not copy_files:
            self.state_notice.setText('WARN：仅引用外部文件，未来移动/更改会影响可重复性。')
        def done(paths):
            if self.project!=project:return
            matches=[i for i in range(self.states.rowCount()) if self.states.item(i,0).text()==sid]
            if len(matches)!=1:return self.fail('输入已复制并登记，但原 state 已变更；请重新选择该输入。')
            r=matches[0]
            current=self.states.item(r,3).text().splitlines();self.states.setItem(r,3,QTableWidgetItem('\n'.join(dict.fromkeys(current+paths))));self.compact_states()
        self.worker(lambda:import_structures(files,project,copy_files),done)
    def build_fast(self):
        v=self.page();f=QFormLayout();self.preset=QComboBox();self.preset.addItems(['Fast Default','Fast Smoke Test','手动设置']);self.preset.currentTextChanged.connect(self.apply_preset);f.addRow('Preset',self.preset)
        self.top_n=QSpinBox();self.top_n.setRange(1,100);self.top_n.setValue(10);f.addRow('fpocket · Top N pockets',self.top_n)
        self.families=QSpinBox();self.families.setRange(1,20);self.families.setValue(3);f.addRow('最大 region families',self.families);self.comparator=QCheckBox('Include comparator');self.comparator.setChecked(True);f.addRow(self.comparator)
        self.molecules=QSpinBox();self.molecules.setRange(1,10000);self.molecules.setValue(100);f.addRow('Molecules / target',self.molecules);self.seed=QSpinBox();self.seed.setRange(0,2147483647);self.seed.setValue(42);f.addRow('Seed',self.seed);self.depth=QComboBox();self.depth.setEditable(True);self.depth.addItems(['2','1','3','4','5','Auto']);f.addRow('Generation depth',self.depth);v.addLayout(f)
        advanced=QGroupBox('Advanced · Region matching');advanced.setCheckable(True);advanced.setChecked(False);av=QVBoxLayout(advanced);content=QWidget();av.addWidget(content);a=QFormLayout(content);self.centroid=QDoubleSpinBox();self.centroid.setRange(.1,100);self.centroid.setValue(6);self.jaccard=QDoubleSpinBox();self.jaccard.setRange(0,1);self.jaccard.setSingleStep(.05);self.jaccard.setValue(.3);self.sensitivity=QCheckBox('Sensitivity analysis');a.addRow('Centroid cutoff (Å)',self.centroid);a.addRow('Residue Jaccard',self.jaccard);a.addRow(self.sensitivity);content.setVisible(False);advanced.toggled.connect(content.setVisible);v.addWidget(advanced)
        self.import_note=label('');v.addWidget(self.import_note);row=QHBoxLayout();row.addWidget(button('保存并校验',self.save_config));row.addWidget(button('查看 / 编辑 YAML',self.yaml_dialog));v.addLayout(row);v.addStretch()
        self.molecules.valueChanged.connect(self.sync_preset);self.seed.valueChanged.connect(self.sync_preset);self.depth.currentTextChanged.connect(self.sync_preset)
    def sync_preset(self,*_):
        name='手动设置'
        if self.seed.value()==42 and self.depth.currentText()=='2':
            if self.molecules.value()==100:name='Fast Default'
            if self.molecules.value()==20:name='Fast Smoke Test'
        self.preset.blockSignals(True);self.preset.setCurrentText(name);self.preset.blockSignals(False)
    def apply_preset(self,name):
        if not hasattr(self,'molecules'):return
        if name=='手动设置':return
        self.molecules.setValue(20 if name=='Fast Smoke Test' else 100);self.seed.setValue(42);self.depth.setCurrentText('2')
        self.sync_preset()
    def collect(self):
        if self.data is None:raise ValueError('请先创建或打开项目')
        d=copy.deepcopy(self.data);states={}
        for i in range(self.states.rowCount()):
            x=[self.states.item(i,j).text().strip() if self.states.item(i,j) else '' for j in range(5)];safe_name(x[0])
            if x[0] in states:raise ValueError('Duplicate state ID')
            states[x[0]]=dict(label=x[1],order=int(x[2]),structures=[to_wsl(Path(to_windows(p)) if Path(to_windows(p)).is_absolute() else self.project/p) for p in x[3].splitlines() if p.strip()],metadata=json.loads(x[4] or '{}'))
        d['protein']['states']=states
        if self.name.text()!=d['project']['name']:raise ValueError('现有项目请使用「复制为新项目」改名，避免输出路径混淆')
        d.setdefault('generation',{}).update(molecules=self.molecules.value(),seed=self.seed.value(),iteration='auto' if self.depth.currentText().lower()=='auto' else int(self.depth.currentText()))
        d.setdefault('region_discovery',{}).update(engine='fpocket',top_n=self.top_n.value());d.setdefault('target_selection',{}).update(max_region_families=self.families.value(),include_comparator=self.comparator.isChecked());d.setdefault('region_matching',{}).update(centroid_cutoff_A=self.centroid.value(),residue_jaccard_min=self.jaccard.value(),sensitivity_analysis=self.sensitivity.isChecked())
        return d
    def yaml_dialog(self):
        try:d=self.collect()
        except Exception as e:return self.fail(str(e))
        dialog=QDialog(self);dialog.setWindowTitle('project.yml · 编辑后必须 backend validate');dialog.resize(850,650);v=QVBoxLayout(dialog);editor=QPlainTextEdit(dump_yaml(d));v.addWidget(editor);b=QDialogButtonBox(QDialogButtonBox.Save|QDialogButtonBox.Cancel);v.addWidget(b);b.accepted.connect(dialog.accept);b.rejected.connect(dialog.reject)
        if dialog.exec()==QDialog.Accepted:
            self.yaml_invalid=True;self.run_button.setEnabled(False)
            try:self.save_config(data=parse_yaml(editor.toPlainText()))
            except Exception as e:self.fail(str(e))
    def save_config(self,checked=False,data=None,after=None):
        try:
            if self.bridge.busy:raise ValueError('请等待当前操作完成')
            if self.project and (self.project/'.pathpocket_gui.lock').exists():raise ValueError('项目已有正在运行的 GUI task；禁止修改活动配置。')
            d=data or self.collect();lightweight_validate(d,self.project)
            output=guard(to_windows(d['project'].get('output_root',self.project)),Path(self.settings['root'])/'20_PROJECTS')
            if output!=self.project.resolve():raise ValueError('配置 output_root 必须等于当前项目目录')
            if d.get('generation',{}).get('iteration')=='auto' and not self.auto_confirmed:
                answer=QMessageBox.warning(self,'Auto generation depth','Auto generation depth may confound state comparisons because ED2Mol changes growth steps according to predicted ED volume.',QMessageBox.Ok|QMessageBox.Cancel)
                if answer!=QMessageBox.Ok:return
                self.auto_confirmed=True
            self.candidate_data=d;self.candidate=self.project/('gui_candidate_'+uuid.uuid4().hex+'.yml');atomic_text(self.candidate,dump_yaml(d));self.after=after;self.call('validate',[to_wsl(self.candidate)],self.project,'save')
        except Exception as e:self.fail(str(e))
    def build_run(self):
        v=self.page();self.run_status=label('Backend：尚未检查；项目：尚未验证');v.addWidget(self.run_status);v.addWidget(label('Validate → Structure QC → Alignment → Regions → Targets → ED2Mol → QC / Chemical space → Report'))
        row=QHBoxLayout();self.run_button=button('运行 Fast Screening',self.run_clicked);self.stop_button=button('停止当前 run',self.stop_run);self.stop_button.setEnabled(False);row.addWidget(self.run_button);row.addWidget(self.stop_button);row.addWidget(button('Backend Doctor',self.doctor));v.addLayout(row)
        self.bar=QProgressBar();v.addWidget(self.bar);self.current=label('尚未运行 · 不预测 ETA');v.addWidget(self.current);self.steps=table(['阶段','状态']);self.steps.setEditTriggers(QAbstractItemView.NoEditTriggers);fill(self.steps,[[name,'NOT RUN'] for _,name in STEPS]);v.addWidget(self.steps,1)
        row=QHBoxLayout();row.addWidget(button('打开 Run 文件夹',lambda:self.open_local(self.loaded_run)));row.addWidget(button('打开调用日志',lambda:self.open_local(self.session)));row.addWidget(button('复制错误摘要',lambda:QApplication.clipboard().setText(self.error_text)));v.addLayout(row)
        logs=QGroupBox('Technical details / stdout / stderr（诊断用途）');logs.setCheckable(True);logs.setChecked(False);lv=QVBoxLayout(logs);self.log=QPlainTextEdit();self.log.setReadOnly(True);self.log.setMaximumHeight(160);self.log.setVisible(False);logs.toggled.connect(self.log.setVisible);lv.addWidget(self.log);v.addWidget(logs)
    def call(self,cmd,args,project,task):
        self.error_text='';self.task=task;self.session=self.bridge.start(cmd,args,project);self.run_status.setText('RUNNING · '+cmd);self.statusBar().showMessage('后台执行 '+cmd)
    def doctor(self):
        try:self.call('doctor',[],None,'doctor')
        except Exception as e:self.fail(str(e))
    def run_clicked(self):
        if self.yaml_invalid:return self.fail('YAML 尚未通过校验；请修正并保存，或重新打开已保存配置。')
        self.nav.setCurrentRow(3);self.save_config(after='run')
    def begin_run(self):
        self.active_run=True;self.lock_editors(True);self.started_at=time.monotonic();self.last_events=[];self.loaded_run=None;self.bar.setValue(0);fill(self.steps,[[name,'NOT RUN'] for _,name in STEPS]);self.run_button.setEnabled(False);self.stop_button.setEnabled(True);self.call('run',[to_wsl(self.project/'project.yml')],self.project,'run')
    def stop_run(self):
        self.bridge.stop();self.run_status.setText('停止请求已发送；保留日志和部分结果，不关闭 WSL');self.stop_button.setEnabled(False)
    def tick(self):
        if self.bridge.busy and self.session and not self.polling:
            self.polling=True;self.workers.append(background(lambda:poll_session(self.session),self.show_poll,self.poll_error))
    def poll_error(self,msg):self.polling=False;self.log.appendPlainText('读取进度重试: '+msg)
    def show_poll(self,p):
        self.polling=False;self.log.setPlainText(p['logs']);events=p['events'];self.last_events=events
        if p['run']:self.loaded_run=p['run']
        if not events:return
        by={e['step']:e for e in events}
        for i,(key,_) in enumerate(STEPS):self.steps.setItem(i,1,QTableWidgetItem(by.get(key,{}).get('status','NOT RUN').upper()))
        passed=sum(by.get(k,{}).get('status')=='PASS' for k,_ in STEPS);self.bar.setValue(round(passed/len(STEPS)*100))
        e=events[-1];elapsed=int(time.monotonic()-self.started_at) if self.started_at else 0
        self.current.setText(f"{e['step']} · {e['status']} · {elapsed//60:02}:{elapsed%60:02} elapsed\n{e.get('target_id','')} {e['message']}")
    def on_complete(self,r):
        task=self.task;self.statusBar().showMessage(task+' · '+r['status'])
        if r.get('run_path'):self.loaded_run=to_windows(r['run_path'])
        if r['status']!='PASS':
            if task.startswith('doctor'):
                self.doctor_data=r.get('data',{});fill(self.doctor_table,[[k,'PASS' if v else 'FAIL'] for k,v in self.doctor_data.get('checks',{}).items()]);self.backend_label.setText('Backend doctor FAIL')
            if r['status']=='INTERRUPTED':self.fail('INTERRUPTED：当前任务已停止，部分结果已保留。GUI session 为取消状态权威记录。')
            else:self.fail(('Failed step: '+self.last_events[-1]['step']+'\n' if task=='run' and self.last_events else '')+r.get('error','Backend failed'))
            self.refresh_history()
            return
        if task=='init':
            p,source=self.pending_create;(p/'runs').mkdir(exist_ok=True);self.project=p
            if source:self.worker(lambda:self.clone_inputs(p,source),self.populate)
            else:self.open_project(p)
        elif task=='save':
            self.yaml_invalid=False;self.run_button.setEnabled(True)
            archive=self.project/'config_history';archive.mkdir(exist_ok=True);shutil.copy2(self.project/'project.yml',archive/('project_'+uuid.uuid4().hex+'.yml'));atomic_text(self.project/'project.yml',dump_yaml(self.candidate_data));write_json(self.project/'gui_project.json',dict(description=self.description.text()));self.data=self.candidate_data
            self.run_status.setText('项目校验 PASS · 已保存 project.yml');self.state_notice.setText('Backend validate PASS');next_action=self.after;self.after=None
            if next_action=='run':self.call('doctor',[],None,'doctor_run')
            else:self.populate(self.data)
        elif task in ['doctor','doctor_run']:
            d=r.get('data',{});self.doctor_data=d;fill(self.doctor_table,[[k,'PASS' if v else 'FAIL'] for k,v in d.get('checks',{}).items()]);self.backend_label.setText('PathPocket backend '+r.get('backend_version','(manifest version at Results)')+' · doctor '+('PASS' if d.get('passed') else 'FAIL')+'\n'+str(d.get('gpu',''))+' · PyTorch '+str(d.get('pytorch','')))
            if not d.get('passed'):return self.fail('doctor failed')
            self.run_status.setText('Backend doctor PASS')
            if task=='doctor_run':self.begin_run()
        elif task=='run':
            self.active_run=False;self.lock_editors(False);self.run_button.setEnabled(True);self.stop_button.setEnabled(False)
            if not self.loaded_run:return self.fail('Run discovery missing / ambiguous')
            self.load_results(self.loaded_run,automatic=True);self.refresh_history()
    def build_results(self):
        v=self.page();self.result_header=label('从 Run history 选择已有 run，或运行完成后自动读取结果。');v.addWidget(self.result_header);self.cards=label('');self.cards.setStyleSheet('font-size:15px;font-weight:600;padding:10px;background:#e4eef0;color:#183844');v.addWidget(self.cards);self.scope_banner=label('Scientific Scope：低精度筛选；分子不等于 confirmed binder；Q-score 不等于 affinity。');v.addWidget(self.scope_banner)
        row=QHBoxLayout();row.addWidget(button('完整 HTML 报告',lambda:self.open_report('html')));row.addWidget(button('Markdown 报告',lambda:self.open_report('md')));row.addWidget(button('打开 Run 目录',lambda:self.open_local(self.loaded_run)));v.addLayout(row)
        self.result_tabs=QTabWidget();v.addWidget(self.result_tabs,1);self.summary_table=table(['Family','State','Generated','Valid unique','ED volume','Median Q norm','Diversity','Scaffolds']);self.summary_table.setEditTriggers(QAbstractItemView.NoEditTriggers);self.result_tabs.addTab(self.summary_table,'汇总表')
        self.gallery_scroll=QScrollArea();self.gallery_scroll.setWidgetResizable(True);self.gallery_widget=QWidget();self.gallery_layout=QGridLayout(self.gallery_widget);self.gallery_scroll.setWidget(self.gallery_widget);self.result_tabs.addTab(self.gallery_scroll,'图集 / Figures');self.scope=QPlainTextEdit();self.scope.setReadOnly(True);self.result_tabs.addTab(self.scope,'Warnings / Scientific Scope')
    def load_results(self,run,automatic=False):
        if self.active_run:return self.fail('运行期间请在 Run 页面查看进度，完成后可切换历史结果。')
        self.worker(lambda:load_run(run),lambda r:self.show_results(r,automatic))
    def show_results(self,r,automatic=False):
        self.result=r;self.loaded_run=r['run'];s=r['summary'];m=r['manifest'];self.result_header.setText(f"{s['project']} · {s['run_id']} · {r['status']}\nBackend {m.get('pathpocket_version','NA')} · commit {m.get('git_commit','NA')[:12]} · States: "+', '.join(s['states']))
        self.result_header.setText(self.result_header.text()+'\nFamilies: '+', '.join(x['region_family_id']+' ('+x.get('role','')+')' for x in s['selected_region_families']))
        k=s['key_metrics'];self.cards.setText(f"Targets  {len(s['targets'])}     Generated  {k.get('generated','NA')}     Valid unique  {k.get('valid_unique_within_targets','NA')}     Physical-compatible  {k.get('physical_compatible_unique','NA')}\nFamilies  {len(s['selected_region_families'])}     Warnings  {len(s['warnings'])+len(r['warnings'])}")
        rows=[]
        for x in s['generation_summary']:
            dv=r['diversity'].get((x['region_family_id'],x['state_id']),{})
            rows.append([x['region_family_id'],x['state_id'],x.get('generated'),x.get('unique'),pretty(x.get('predicted_ED_volume')),pretty(x.get('median_Q_normalized')),pretty(float(dv['within_state_diversity'])) if dv.get('within_state_diversity') else 'NA',dv.get('scaffold_count','NA')])
        fill(self.summary_table,rows);self.scope.setPlainText('Warnings\n'+'\n'.join(s['warnings']+r['warnings'])+'\n\nScientific Scope\n'+'\n'.join(s['limitations']));self.build_gallery(r['figures']);self.nav.setCurrentRow(4);self.run_status.setText('结果 '+r['status']);self.bar.setValue(100 if m.get('status')=='COMPLETE' else self.bar.value())
        if automatic and self.settings['open_report']:self.open_report('html')
    def build_gallery(self,figures):
        while self.gallery_layout.count():
            item=self.gallery_layout.takeAt(0)
            if item.widget():item.widget().deleteLater()
        for i,f in enumerate(figures):
            box=QGroupBox(f['name']);v=QVBoxLayout(box);preview=QPushButton('读取缩略图…');preview.setMinimumHeight(195);preview.setIconSize(QSize(340,170));preview.setToolTip('点击打开完整原图');preview.clicked.connect(lambda checked=False,p=f['path']:self.open_local(p));v.addWidget(preview)
            def thumb(p=f['path']):
                reader=QImageReader(p);reader.setScaledSize(reader.size().scaled(QSize(340,170),Qt.KeepAspectRatio));return reader.read()
            def loaded(img,w=preview):
                if img.isNull():w.setText('WARN · figure missing / unreadable')
                else:w.setIcon(QIcon(QPixmap.fromImage(img)));w.setText('')
            self.worker(thumb,loaded);row=QHBoxLayout()
            for ext in ['csv','svg','pdf']:
                b=button(ext.upper(),lambda checked=False,p=f['related'].get(ext):self.open_local(p));b.setEnabled(ext in f['related']);row.addWidget(b)
            v.addLayout(row);v.addWidget(button('所在文件夹',lambda checked=False,p=str(Path(f['path']).parent):self.open_local(p)));self.gallery_layout.addWidget(box,i//2,i%2)
    def open_local(self,path):
        if not path or not Path(path).exists():self.fail('文件缺失 / missing: '+str(path));return False
        ok=QDesktopServices.openUrl(QUrl.fromLocalFile(str(Path(path).resolve())))
        if not ok:self.fail('Windows 默认程序无法打开该文件')
        return ok
    def open_report(self,kind):
        return self.open_local(self.result['reports'].get(kind)) if self.result else False
    def build_settings(self):
        v=self.page();f=QFormLayout();self.setting_fields={}
        for key,text in [('root','Canonical Root'),('distro','WSL Distribution'),('launcher','Backend launcher'),('project_parent','Default Project Parent')]:
            w=QLineEdit(self.settings[key]);self.setting_fields[key]=w;f.addRow(text,w)
        self.open_after=QCheckBox('运行完成后打开 HTML 报告');self.open_after.setChecked(self.settings['open_report']);f.addRow(self.open_after);self.theme=QComboBox();self.theme.addItems(['System','Light','Dark']);self.theme.setCurrentText(self.settings['theme']);f.addRow('Theme',self.theme);v.addLayout(f)
        row=QHBoxLayout();row.addWidget(button('保存设置',self.save_preferences));row.addWidget(button('重新发现 WSL',self.discover));row.addWidget(button('Run Backend Doctor',self.doctor));v.addLayout(row);self.backend_label=label('正在检查 WSL…');v.addWidget(self.backend_label);self.doctor_table=table(['检查项','状态']);self.doctor_table.setEditTriggers(QAbstractItemView.NoEditTriggers);v.addWidget(self.doctor_table,1);v.addWidget(label('PathPocket GUI v0.1.0 · PathPocket backend v0.1.0\nFast Screening prototype — For low-precision screening and hypothesis generation.\n离线使用 · 无 telemetry · 不上传数据 · 无自动更新'))
    def save_preferences(self):
        try:
            if self.bridge.busy:raise ValueError('后台操作期间不能修改设置')
            s=dict(self.settings);s.update({k:v.text() for k,v in self.setting_fields.items()});s.update(open_report=self.open_after.isChecked(),theme=self.theme.currentText());save_settings(s);self.settings=s;self.bridge.settings=s;self.apply_theme();self.statusBar().showMessage('设置已保存到 Windows 用户配置目录')
        except Exception as e:self.fail(str(e))
    def apply_theme(self):
        theme=self.settings.get('theme','System')
        if theme=='Dark':self.setStyleSheet('QWidget{background:#23292e;color:#e2e8ee} QLineEdit,QPlainTextEdit,QTableWidget,QListWidget{background:#182127} QPushButton{padding:7px;background:#34454f} QHeaderView::section{background:#34454f;}')
        elif theme=='Light':self.setStyleSheet('QWidget{background:#f7f8fa;color:#182631} QLineEdit,QPlainTextEdit,QTableWidget,QListWidget{background:white} QPushButton{padding:7px} QHeaderView::section{background:#e9eef2;}')
        else:self.setStyleSheet('QPushButton{padding:7px} QGroupBox{margin-top:8px}')
    def discover(self):
        if os.name!='nt':
            self.backend_label.setText('包内 Linux backend')
            if not self.bridge.busy:self.doctor()
            return
        def find():
            if not shutil.which('wsl.exe'):raise ValueError('WSL unavailable')
            p=subprocess.run(['wsl.exe','--list','--quiet'],capture_output=True,timeout=30,creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0));names=p.stdout.decode('utf-16-le',errors='replace').replace('\x00','').splitlines();return [x.strip() for x in names if x.strip()]
        def done(names):
            self.backend_label.setText('可用 WSL：'+', '.join(names)+'\n推荐 / 当前：'+self.settings['distro'])
            if self.settings['distro'] not in names:return self.fail('WSL distribution 不存在，请在设置中选择可用名称')
            if not self.bridge.busy:self.doctor()
        self.worker(find,done)
    def closeEvent(self,event):
        if self.bridge.busy:
            QMessageBox.information(self,'后台任务仍在运行','请先点击停止并等待任务退出，或保持窗口打开。');event.ignore()
        else:event.accept()

from .polish import Window

def main():
    import argparse
    parser=argparse.ArgumentParser(description='PathPocket Windows Fast Screening GUI');parser.add_argument('--startup-check',help='Write a real GUI startup/doctor acceptance record in a new canonical round QC directory');parser.add_argument('--project');args=parser.parse_args()
    app=QApplication(sys.argv);app.setApplicationName('PathPocket');app.setOrganizationName('PathPocket');w=Window();w.show()
    if args.project:QTimer.singleShot(500,lambda:w.open_project(to_windows(args.project)))
    if args.startup_check:
        out=guard(args.startup_check,ROOT/'10_ROUNDS'/ROUND);out.mkdir(parents=True,exist_ok=False);start=time.monotonic();timer=QTimer(w)
        def check():
            if not w.bridge.busy and (hasattr(w,'doctor_data') or w.error_text) or time.monotonic()-start>120:
                passed=bool(getattr(w,'doctor_data',{}).get('passed')) and not w.error_text;w.nav.setCurrentRow(5);w.grab().save(str(out/'startup.png'));write_json(out/'startup.json',dict(passed=passed,frozen=bool(getattr(sys,'frozen',False)),executable=sys.executable,gui_version=__version__,doctor=getattr(w,'doctor_data',{}),error=w.error_text));timer.stop();app.exit(0 if passed else 1)
        timer.timeout.connect(check);timer.start(500)
    sys.exit(app.exec())
