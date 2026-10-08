"""Presentation refinements. Reuses the validated GUI model and CLI bridge."""
import csv,io,time,json,subprocess
from pathlib import Path
from PySide6.QtCore import Qt,QTimer,QSize
from PySide6.QtGui import QFont,QShortcut,QKeySequence,QColor,QPixmap,QImageReader,QIcon
from PySide6.QtWidgets import *
from .app import Window as BaseWindow,button,label,table,fill,STEPS
from .storage import ROOT,ROUND,read_json,write_json,to_windows,sha,inside

def card(title):
    box=QGroupBox(title);layout=QVBoxLayout(box);layout.setSpacing(8);return box,layout

def fold(title,widget):
    box,layout=card(title);box.setCheckable(True);box.setChecked(False);layout.addWidget(widget);widget.hide();box.setMaximumHeight(34)
    def toggle(checked):widget.setVisible(checked);box.setMaximumHeight(16777215 if checked else 34)
    box.toggled.connect(toggle);return box

class NumericItem(QTableWidgetItem):
    def __lt__(self,other):
        try:return float(self.text())<float(other.text())
        except ValueError:return self.text()<other.text()

class FigureViewer(QDialog):
    def __init__(self,path,parent):
        super().__init__(parent);self.path=path;self.pix=QPixmap(path);self.scale=1.;self.setWindowTitle(Path(path).name);self.resize(1000,720)
        v=QVBoxLayout(self);row=QHBoxLayout();v.addLayout(row)
        for text,fn in [('适应窗口',self.fit),('100%',lambda:self.zoom(1)),('放大 +',lambda:self.zoom(self.scale*1.25)),('缩小 −',lambda:self.zoom(self.scale/1.25)),('外部打开',lambda:parent.open_local(path))]:row.addWidget(button(text,fn))
        self.scroll=QScrollArea();self.image=QLabel();self.image.setAlignment(Qt.AlignCenter);self.scroll.setWidget(self.image);v.addWidget(self.scroll,1);QTimer.singleShot(0,self.fit)
    def fit(self):
        if self.pix.isNull():self.image.setText('图像无法读取');return
        size=self.scroll.viewport().size();self.zoom(min(size.width()/self.pix.width(),size.height()/self.pix.height()))
    def zoom(self,value):
        self.scale=max(.05,min(8,value));size=self.pix.size()*self.scale;self.image.setPixmap(self.pix.scaled(size,Qt.KeepAspectRatio,Qt.SmoothTransformation));self.image.resize(size)

class Window(BaseWindow):
    def __init__(self,settings=None):
        self._populating=False;self._preset=False;self._details=False;self.history_all=False;self.thumbnail_queue=[];self.thumbnails_loaded=0
        super().__init__(settings);self.setWindowTitle('PathPocket GUI v0.1.6 (portable transport) — Fast Screening')
        top=self.centralWidget().layout();title=top.itemAt(0).widget();top.removeWidget(title);title.deleteLater();header=QWidget();hr=QHBoxLayout(header);hr.setContentsMargins(0,0,0,0);title=label('PathPocket');title.setStyleSheet('font-size:17px;font-weight:600');hr.addWidget(title);badge=label('Fast Screening');badge.setStyleSheet('font-size:11px;color:#286f79;background:#dceef0;border-radius:8px;padding:3px 9px');hr.addWidget(badge);hr.addStretch();top.insertWidget(0,header);top.itemAt(1).widget().setText('低精度筛选与假设生成 · GUI → PathPocket backend')
        self.nav.setFixedWidth(200);self.nav.setObjectName('navigation');self.nav.setSpacing(3)
        self.page_status=[]
        for i in range(self.pages.count()):
            notice=label('○ NOT RUN · 请先打开项目' if i<5 else '○ NOT RUN · 正在检查 backend');notice.setObjectName('notice');self.pages.widget(i).layout().insertWidget(0,notice);self.page_status.append(notice)
        for key,fn in [('Ctrl+N',self.new_dialog),('Ctrl+O',self.open_dialog),('Ctrl+S',self.save_config),('F5',self.refresh_current)]:QShortcut(QKeySequence(key),self,activated=fn)
        self.update_nav();self.timer.timeout.connect(self.update_run_header)
        self.run_button.setEnabled(bool(self.data))
        self.worker(self.commit_info,lambda text:self.about.setText(self.about.text()+'\n'+text))
        if self.settings.get('remember_project') and self.settings.get('recent'):
            p=Path(self.settings['recent'][0])
            if (p/'project.yml').is_file():self.open_project(p)

    def apply_theme(self):
        dark=self.settings.get('theme')=='Dark' or (self.settings.get('theme')=='System' and QApplication.styleHints().colorScheme()==Qt.ColorScheme.Dark);self.dark_theme=dark;bg='#20292e' if dark else '#f2f5f6';surface='#29353b' if dark else '#ffffff';fg='#e3eaed' if dark else '#243840';border='#46565e' if dark else '#d7e1e5';selected='#31545c' if dark else '#dceef0'
        self.setFont(QFont('Microsoft YaHei UI',9));self.setStyleSheet(f'''
        QWidget{{color:{fg};}} QMainWindow,QStackedWidget{{background:{bg};}}
        QGroupBox{{background:{surface};border:1px solid {border};border-radius:5px;margin-top:10px;padding:10px 8px 6px;font-weight:600;}}
        QGroupBox::title{{subcontrol-origin:margin;left:10px;padding:0 4px;}}
        QLineEdit,QComboBox,QSpinBox,QDoubleSpinBox,QPlainTextEdit,QTableWidget,QListWidget{{background:{surface};border:1px solid {border};border-radius:3px;padding:3px;}}
        QPushButton{{background:{surface};border:1px solid {border};border-radius:4px;padding:6px 11px;min-height:20px;}}
        QPushButton:hover{{border-color:#488e97;background:{selected};}} QPushButton:disabled{{color:#88969a;}}
        QPushButton[primary="true"]{{background:#286f79;color:white;border-color:#286f79;font-weight:600;}}
        QHeaderView::section{{background:{bg};padding:6px;border:0;border-bottom:1px solid {border};font-weight:600;}}
        QTableWidget{{gridline-color:{border};selection-background-color:{selected};selection-color:{fg};}}
        QListWidget#navigation{{background:{bg};border:0;padding:4px;}}
        QListWidget#navigation::item{{padding:13px 7px;border-radius:4px;}}
        QListWidget#navigation::item:selected{{background:{selected};color:{fg};font-weight:600;border-left:3px solid #287a84;}}
        QLabel#notice{{padding:5px 8px;border-left:3px solid #54939a;background:{selected};}}
        QProgressBar{{border:1px solid {border};border-radius:4px;text-align:center;min-height:19px;}}
        QProgressBar::chunk{{background:#54939a;}} QTabBar::tab{{padding:7px 18px;}}
        ''')
    def update_nav(self):
        run_mark='●' if self.bridge.busy else ('×' if self.error_text else '✓' if getattr(self,'last_run_status','')=='PASS' else '○');doctor_mark='✓' if getattr(self,'doctor_data',{}).get('passed') else ('×' if hasattr(self,'doctor_data') else '○')
        marks=['✓' if self.project else '○','✓' if self.data else '○','✓' if self.data else '○',run_mark,('!' if self.result.get('warnings') else '✓') if self.result else '○',doctor_mark]
        for i,text in enumerate(['项目 Project','蛋白状态','Fast 参数','运行 Run','结果 Results','设置 / About']):self.nav.item(i).setText(marks[i]+'  '+text)
    def refresh_current(self):
        self.refresh_history()
        if self.pages.currentIndex()==4 and self.result:self.load_results(self.result['run'])
        elif self.pages.currentIndex()==5 and not self.bridge.busy:self.doctor()
    def fail(self,message):
        super().fail(message)
        if hasattr(self,'page_status'):
            self.page_status[self.pages.currentIndex()].setText('× FAIL · '+self.human_error(message));self.page_status[3].setText('× FAIL · '+self.human_error(message));self.update_nav()
    def build_project(self):
        v=self.page();box,fv=card('项目');f=QFormLayout();self.name=QLineEdit();self.path_label=label('尚未打开项目');self.description=QLineEdit();f.addRow('项目名称',self.name);f.addRow('项目目录',self.path_label);f.addRow('说明',self.description);fv.addLayout(f)
        row=QHBoxLayout();b=button('新建项目',self.new_dialog);b.setProperty('primary',True);row.addWidget(b)
        for t,fn in [('打开项目',self.open_dialog),('复制为新项目',self.clone_dialog)]:row.addWidget(button(t,fn))
        row.addStretch();fv.addLayout(row);self.project_hint=label('尚未打开项目。新建一个项目，或打开已有 PathPocket 项目开始 Fast Screening。');fv.addWidget(self.project_hint);v.addWidget(box)
        self.recent=table(['项目名称','路径','最后打开','状态']);self.recent.setEditTriggers(QAbstractItemView.NoEditTriggers);self.recent.setMaximumHeight(150);self.recent.horizontalHeader().setSectionResizeMode(1,QHeaderView.Stretch);self.recent.cellDoubleClicked.connect(lambda r,c:self.open_project(Path(self.recent.item(r,1).text())));v.addWidget(label('最近项目 · 最多显示 5 项'));v.addWidget(self.recent);self.recent_empty=label('暂无最近项目');v.addWidget(self.recent_empty);self.fill_recent()
        row=QHBoxLayout();history_title=label('Run History · 双击查看只读结果');history_title.setMinimumWidth(350);row.addWidget(history_title);row.addStretch();row.addWidget(button('查看全部 / 最近',self.toggle_history));row.addWidget(button('刷新',self.refresh_history));v.addLayout(row)
        self.history_table=table(['Run ID','时间','状态','Profile','报告']);self.history_table.setEditTriggers(QAbstractItemView.NoEditTriggers);self.history_table.setMaximumHeight(220);self.history_table.cellDoubleClicked.connect(lambda r,c:self.load_results(self.history_rows[r]['path']));v.addWidget(self.history_table);self.history_empty=label('尚无运行记录。完成配置后前往 Run 页面。');v.addWidget(self.history_empty);v.addStretch()
    def fill_recent(self):
        recent=self.settings.get('recent',[])[:5];meta=self.settings.get('recent_metadata',{});fill(self.recent,[[Path(p).name,p,meta.get(p,{}).get('opened','—'),'可打开' if (Path(p)/'project.yml').exists() else '缺失'] for p in recent]);self.recent_empty.setVisible(not recent);self.recent.setVisible(bool(recent))
        self.recent.verticalHeader().setDefaultSectionSize(26);self.recent.setFixedHeight(38+min(len(recent),5)*26)
    def toggle_history(self):self.history_all=not self.history_all;self.refresh_history()
    def show_history(self,rows):
        self.history_rows=rows if self.history_all else rows[:6];fill(self.history_table,[[r['run_id'],r['date'][:19].replace('T',' '),r['status'],'Fast Screening','HTML' if r['report'] else '—'] for r in self.history_rows]);self.history_empty.setVisible(not rows);self.history_table.setVisible(bool(rows))
        self.history_table.verticalHeader().setDefaultSectionSize(26);self.history_table.setFixedHeight(38+min(len(self.history_rows),6)*26)
    def populate(self,d):
        self._populating=True
        try:super().populate(d)
        finally:self._populating=False
        if self.result and (self.result.get('summary') or {}).get('project')!=d['project']['name']:
            self.result=None;self.loaded_run=None;self.result_header.setText('当前项目尚无可展示结果。');self.history_badge.setText('○ NOT RUN');self.summary_table.setRowCount(0);self.build_gallery([]);self.scope.clear();self.warning_summary.setText('暂无结果警告');self.result_tabs.hide();self.mapping_status.setText('Mapping data not available for this historical run');self.mapping_button.setEnabled(False);self.structure_status.setText('Structure Mode: historical adapter data unavailable');self.aggregate_qc_button.setEnabled(False);self.repeat_mapping_button.setEnabled(False)
            for number in self.metric_cards:number.setText('—')
        self.settings.setdefault('recent_metadata',{})[str(self.project)]={'opened':time.strftime('%Y-%m-%d %H:%M')}
        from .app import save_settings
        save_settings(self.settings);self.fill_recent();self.project_hint.setText('✓ 项目已加载 · 保存配置需通过 backend validate');self.result_empty.setVisible(not bool(self.result));self.states.selectRow(0);self.show_state_details();self.refresh_state_counts()
        if hasattr(self,'page_status'):
            for i in [0,1,2]:self.page_status[i].setText('✓ 已加载 · '+self.project.name)
            self.update_nav()
    def update_recent(self):self.fill_recent()
    def commit_info(self):
        release=Path(__file__).resolve().parents[2]/'release_manifest.json'
        if not release.exists():return 'Distribution source archive (build context)'
        d=read_json(release)
        return 'GUI '+d['GUI']['version']+' · Backend '+d['backend']['commit'][:12]+' · archived frozen source'
    def build_states(self):
        super().build_states();v=self.pages.widget(1).layout();v.itemAt(0).widget().setText('选择状态查看结构文件；结构 QC 由 backend 执行。')
        v.removeWidget(self.states);split=QSplitter();split.addWidget(self.states);details=QWidget();dv=QVBoxLayout(details);dv.setContentsMargins(10,0,0,0);dv.addWidget(label('State Details'));self.state_label=QLineEdit();dv.addWidget(self.state_label);self.state_label.textEdited.connect(self.edit_detail_label)
        self.metadata_editor=QPlainTextEdit();self.metadata_editor.setMaximumHeight(100);self.metadata_editor.textChanged.connect(self.edit_metadata);dv.addWidget(fold('Advanced · Metadata (JSON)',self.metadata_editor))
        self.pdb_list=QListWidget();dv.addWidget(self.pdb_list,1);self.pdb_list.currentRowChanged.connect(self.show_pdb_hash);self.hash_label=label('选择结构查看 SHA256');dv.addWidget(fold('SHA256 / 来源',self.hash_label));row=QHBoxLayout()
        for text,fn in [('添加 PDB',self.browse_pdb),('移除',self.remove_pdb),('复制到项目',self.copy_selected_pdb)]:row.addWidget(button(text,fn))
        dv.addLayout(row);split.addWidget(details);split.setSizes([430,480]);v.insertWidget(1,split,1);self.states.setColumnCount(7);self.states.setHorizontalHeaderLabels(['State ID','Label','Order','Structures','Metadata','PDB count','Status']);self.states.hideColumn(3);self.states.hideColumn(4);header=self.states.horizontalHeader();header.moveSection(header.visualIndex(2),0);header.setSectionResizeMode(QHeaderView.ResizeToContents);header.setStretchLastSection(True);self.states.itemSelectionChanged.connect(self.show_state_details);self.states.itemChanged.connect(self.refresh_state_counts)
    def compact_states(self):
        for i in range(self.states.rowCount()):self.states.setRowHeight(i,34)
        if hasattr(self,'pdb_list'):self.show_state_details()
    def refresh_state_counts(self,*_):
        if self._details:return
        self.states.blockSignals(True)
        for i in range(self.states.rowCount()):
            item=self.states.item(i,3);paths=item.text().splitlines() if item else [];n=len([p for p in paths if p.strip()]);self.states.setItem(i,5,QTableWidgetItem(str(n)));self.states.setItem(i,6,QTableWidgetItem('已配置' if n else '待添加'));self.states.setRowHeight(i,34)
            for col in [5,6]:self.states.item(i,col).setFlags(self.states.item(i,col).flags() & ~Qt.ItemIsEditable)
        self.states.blockSignals(False)
    def show_state_details(self):
        if not hasattr(self,'state_label'):return
        r=self.states.currentRow();self._details=True;self.pdb_list.clear();self.hash_label.setText('选择结构查看 SHA256')
        if r>=0 and self.states.item(r,1):
            self.state_label.setText(self.states.item(r,1).text());self.metadata_editor.setPlainText(self.states.item(r,4).text() if self.states.item(r,4) else '{}');paths=self.states.item(r,3).text().splitlines() if self.states.item(r,3) else []
            for path in paths:
                p=Path(to_windows(path));item=QListWidgetItem(p.name+'\n'+('项目副本' if self.project and inside(p,self.project) else '外部引用'));item.setData(Qt.UserRole,str(p));item.setToolTip(str(p));self.pdb_list.addItem(item)
        else:self.state_label.clear();self.metadata_editor.clear()
        self._details=False
    def edit_detail_label(self,text):
        r=self.states.currentRow()
        if r>=0 and not self._details:self.states.setItem(r,1,QTableWidgetItem(text))
    def edit_metadata(self):
        r=self.states.currentRow()
        if r>=0 and not self._details:self.states.setItem(r,4,QTableWidgetItem(self.metadata_editor.toPlainText()))
    def show_pdb_hash(self,r):
        item=self.pdb_list.item(r)
        if not item:return
        p=item.data(Qt.UserRole);self.hash_label.setText('读取中…')
        def done(digest):
            current=self.pdb_list.currentItem()
            if current and current.data(Qt.UserRole)==p:self.hash_label.setText(p+'\n'+digest)
        self.worker(lambda:sha(p),done)
    def remove_pdb(self):
        r=self.states.currentRow();p=self.pdb_list.currentRow()
        if r<0 or p<0:return
        paths=self.states.item(r,3).text().splitlines();paths.pop(p);self.states.setItem(r,3,QTableWidgetItem('\n'.join(paths)));self.show_state_details()
    def copy_selected_pdb(self):
        item=self.pdb_list.currentItem();r=self.states.currentRow()
        if not item or r<0:return
        from .storage import import_structures
        path=item.data(Qt.UserRole);sid=self.states.item(r,0).text();project=self.project
        def done(paths):
            if self.project!=project:return
            rows=[i for i in range(self.states.rowCount()) if self.states.item(i,0).text()==sid]
            if len(rows)!=1:return
            row=rows[0];current=self.states.item(row,3).text().splitlines();current=[paths[0] if to_windows(p)==path else p for p in current];self.states.setItem(row,3,QTableWidgetItem('\n'.join(dict.fromkeys(current))));self.show_state_details()
        self.worker(lambda:import_structures([path],project,True),done)
    def build_fast(self):
        v=self.page();self.preset=QComboBox();self.preset.addItems(['Fast Default','Fast Smoke Test','Custom']);self.preset.currentTextChanged.connect(self.apply_preset);v.addWidget(self.preset)
        a,av=card('A. Region Discovery');f=QFormLayout();self.top_n=QSpinBox();self.top_n.setRange(1,100);self.top_n.setValue(10);self.families=QSpinBox();self.families.setRange(1,20);self.families.setValue(3);self.comparator=QCheckBox('Include comparator');self.comparator.setChecked(True);f.addRow('Top N pockets',self.top_n);f.addRow('最大 region families',self.families);f.addRow(self.comparator);av.addLayout(f);v.addWidget(a)
        advanced=QWidget();f=QFormLayout(advanced);self.centroid=QDoubleSpinBox();self.centroid.setRange(.1,100);self.centroid.setValue(6);self.jaccard=QDoubleSpinBox();self.jaccard.setRange(0,1);self.jaccard.setSingleStep(.05);self.jaccard.setValue(.3);self.sensitivity=QCheckBox('Sensitivity analysis');f.addRow('Centroid cutoff (Å)',self.centroid);f.addRow('Residue Jaccard',self.jaccard);f.addRow(self.sensitivity);v.addWidget(fold('B. Region Matching · Advanced',advanced))
        c,cv=card('C. ED2Mol Challenge');f=QFormLayout();self.molecules=QSpinBox();self.molecules.setRange(1,10000);self.molecules.setValue(100);self.seed=QSpinBox();self.seed.setRange(0,2147483647);self.seed.setValue(42);self.depth=QComboBox();self.depth.setEditable(True);self.depth.addItems(['2','1','3','4','5','Auto']);f.addRow('Molecules / target',self.molecules);f.addRow('Seed',self.seed);f.addRow('Generation depth',self.depth);cv.addLayout(f);v.addWidget(c)
        tips={self.top_n:'每个 receptor 送入区域发现的 pocket 数量。',self.families:'限制进入 Fast Screening 的区域数量。',self.comparator:'保留 backend 选择的 comparator。',self.centroid:'空间匹配的质心距离阈值。',self.jaccard:'匹配残基集合重叠阈值。',self.sensitivity:'由 backend 执行已有 sensitivity analysis。',self.molecules:'每个 target 的请求分子数；实际数量以结果为准。',self.seed:'单一随机种子，用于可重复运行。',self.depth:'固定生长步数，便于不同状态公平比较。Auto 可能引入 growth-depth confounding。'}
        for widget,tip in tips.items():
            widget.setToolTip(tip)
            signal=widget.valueChanged if isinstance(widget,(QSpinBox,QDoubleSpinBox)) else widget.toggled if isinstance(widget,QCheckBox) else widget.currentTextChanged
            signal.connect(self.parameter_edited)
        self.import_note=label('打开项目后显示区域来源');v.addWidget(self.import_note);row=QHBoxLayout();b=button('保存并校验',self.save_config);b.setProperty('primary',True);row.addWidget(b);row.addWidget(button('查看 / 编辑 YAML',self.yaml_dialog));row.addStretch();v.addLayout(row);v.addStretch()
    def parameter_edited(self,*_):
        if not self._populating and not self._preset:self.preset.setCurrentText('Custom')
    def sync_preset(self,*_):
        values=(self.top_n.value(),self.families.value(),self.comparator.isChecked(),self.centroid.value(),self.jaccard.value(),self.sensitivity.isChecked(),self.seed.value(),self.depth.currentText())
        name='Custom'
        if values==(10,3,True,6,.3,False,42,'2'):name={100:'Fast Default',20:'Fast Smoke Test'}.get(self.molecules.value(),'Custom')
        self.preset.blockSignals(True);self.preset.setCurrentText(name);self.preset.blockSignals(False)
    def apply_preset(self,name):
        if name not in ['Fast Default','Fast Smoke Test'] or not hasattr(self,'molecules'):return
        self._preset=True;self.top_n.setValue(10);self.families.setValue(3);self.comparator.setChecked(True);self.centroid.setValue(6);self.jaccard.setValue(.3);self.sensitivity.setChecked(False);self.molecules.setValue(20 if name=='Fast Smoke Test' else 100);self.seed.setValue(42);self.depth.setCurrentText('2');self._preset=False;self.sync_preset()
    def build_run(self):
        super().build_run();v=self.pages.widget(3).layout();v.itemAt(1).widget().hide();self.run_overview=label('Project —   Backend —   Run ID —   Elapsed 00:00:00');v.insertWidget(1,self.run_overview);self.run_button.setProperty('primary',True);self.steps.verticalHeader().hide();self.steps.horizontalHeader().setSectionResizeMode(0,QHeaderView.Stretch);self.steps.setMinimumHeight(190)
        self.log.setFont(QFont('Cascadia Mono',9));self.log.setLineWrapMode(QPlainTextEdit.NoWrap);logs=self.log.parentWidget();logs.setTitle('技术日志（诊断）');self.log_actions=QWidget();row=QHBoxLayout(self.log_actions);row.setContentsMargins(0,0,0,0);self.autoscroll=QCheckBox('自动滚动');self.autoscroll.setChecked(True);row.addWidget(self.autoscroll);row.addWidget(button('复制日志',lambda:QApplication.clipboard().setText(self.log.toPlainText())));row.addWidget(button('清空显示',self.log.clear));logs.layout().insertWidget(0,self.log_actions);self.log_actions.hide();logs.toggled.connect(self.log_actions.setVisible)
        self.view_results_button=button('查看结果',lambda:self.load_results(self.loaded_run));self.view_results_button.setProperty('primary',True);self.view_results_button.hide();v.insertWidget(3,self.view_results_button)
        self.run_doctor_button=next(b for b in self.pages.widget(3).findChildren(QPushButton) if b.text()=='Backend Doctor')
        self.bar.setFormat('Overall Progress · %p%');self.bar.setValue(0)
    def update_run_header(self):
        elapsed=int(time.monotonic()-self.started_at) if self.started_at and self.active_run else getattr(self,'final_elapsed',0);self.run_overview.setText(f"Project: {self.project.name if self.project else '—'}    Backend: {'PASS' if getattr(self,'doctor_data',{}).get('passed') else 'NOT RUN'}\nRun ID: {Path(self.loaded_run).name if self.loaded_run else '—'}    Elapsed: {elapsed//3600:02}:{elapsed//60%60:02}:{elapsed%60:02}");self.update_nav()
    def call(self,*args):
        super().call(*args)
        if hasattr(self,'page_status'):self.page_status[3].setText('● RUNNING · '+args[0]);self.update_nav()
    def begin_run(self):
        super().begin_run();self.view_results_button.hide();self.run_button.hide();self.run_doctor_button.setEnabled(False);self.stop_button.setProperty('primary',True);self.stop_button.style().unpolish(self.stop_button);self.stop_button.style().polish(self.stop_button);self.steps.setItem(0,1,QTableWidgetItem('PASS'))
    def show_poll(self,p):
        pos=self.log.verticalScrollBar().value()
        if self.task=='run' and p['events']:
            p=dict(p,events=[dict(step='GUI_VALIDATE',status='PASS',message='CLI preflight validate passed')]+p['events'])
        super().show_poll(p)
        self.log.verticalScrollBar().setValue(self.log.verticalScrollBar().maximum() if self.autoscroll.isChecked() else pos)
        colors={'PASS':'#28774b','RUNNING':'#287a84','WARN':'#996900','FAIL':'#af3944','NOT RUN':'#73828a'}
        for i in range(self.steps.rowCount()):
            item=self.steps.item(i,1)
            if item:
                state=item.text();item.setForeground(QColor(colors.get(state,'#73828a')))
                for c in range(2):self.steps.item(i,c).setBackground(QColor(('#31545c' if self.dark_theme else '#dceef0') if state=='RUNNING' else ('#29353b' if self.dark_theme else '#ffffff')))
        self.update_run_header()
    def on_complete(self,r):
        completed_task=self.task
        if r.get('status')=='FAIL' and (r.get('run_path') or self.loaded_run):
            from .contracts import load_run
            try:
                stopped=load_run(to_windows(r.get('run_path') or self.loaded_run))
                if stopped.get('run_kind')=='structure_adaptation_stopped':
                    self.active_run=False;self.lock_editors(False);self.run_button.setEnabled(True);self.run_button.show();self.stop_button.setEnabled(False);self.run_doctor_button.setEnabled(True);self.error_text='';self.last_run_status='STOPPED';self.show_results(stopped);self.refresh_history();return
            except (OSError,ValueError):pass
        if r.get('state_write_warning'):self.log.appendPlainText('WARN · GUI heartbeat retry: '+r['state_write_warning'])
        if self.active_run and self.started_at:self.final_elapsed=int(time.monotonic()-self.started_at)
        super().on_complete(r)
        if r.get('status')=='FAIL' and self.loaded_run:
            try:
                manifest=json.loads((Path(self.loaded_run)/'run_manifest.json').read_text(encoding='utf-8-sig'));mapping=manifest.get('residue_mapping',{})
                if mapping.get('status') in ['AMBIGUOUS','LOW_CONFIDENCE','UNSUPPORTED_RESIDUE']:
                    text='Residue Mapping · FAIL · '+mapping['status'];self.mapping_status.setText(text);self.state_notice.setText(text);self.mapping_status.setToolTip(mapping.get('error',''));self.mapping_button.setEnabled(False)
            except (OSError,ValueError):pass  # Existing run failure diagnostics remain visible.
        if completed_task=='run':self.last_run_status=r['status']
        if not self.active_run:
            self.run_button.show();self.run_doctor_button.setEnabled(True);self.stop_button.setProperty('primary',False);self.stop_button.style().unpolish(self.stop_button);self.stop_button.style().polish(self.stop_button)
        if hasattr(self,'page_status'):
            self.page_status[3].setText(('● RUNNING · '+self.task) if self.bridge.busy else (('✓ PASS' if r['status']=='PASS' else '× '+r['status'])+' · '+completed_task))
            if completed_task.startswith('doctor'):
                self.page_status[5].setText('✓ Doctor PASS' if getattr(self,'doctor_data',{}).get('passed') else '× Doctor FAIL');self.doctor_detail.setPlainText(json.dumps(r,ensure_ascii=False,indent=2))
                checks=getattr(self,'doctor_data',{}).get('checks',{});names={'WSL':'WSL','python':'Python','GPU':'GPU','PyTorch':'PyTorch','fpocket':'fpocket','ED2Mol_import':'ED2Mol','ED2Mol_weights':'Weights','disk_space':'Disk','canonical_workspace':'Workspace'};keys=[k for k in names if k in checks]+[k for k in checks if k not in names];fill(self.doctor_table,[[names.get(k,k),'PASS' if checks[k] else 'FAIL'] for k in keys]);self.doctor_table.verticalHeader().setDefaultSectionSize(24)
                for i,k in enumerate(keys):self.doctor_table.item(i,1).setForeground(QColor('#28774b' if checks[k] else '#af3944'))
            self.update_nav()
    def build_results(self):
        v=self.page();self.result_header=label('当前项目尚无可展示结果。');v.addWidget(self.result_header);self.history_badge=label('○ NOT RUN');v.addWidget(self.history_badge);self.result_empty=button('完成一次 Fast Screening 后显示 summary、figures 和 report → 前往运行',lambda:self.nav.setCurrentRow(3));v.addWidget(self.result_empty)
        row=QHBoxLayout();self.metric_cards=[]
        for title in ['Region Families','Targets','Generated','Valid Unique','Physical-Compatible','Warnings']:
            box,cv=card(title);number=label('—');number.setAlignment(Qt.AlignCenter);number.setStyleSheet('font-size:24px;font-weight:600');cv.addWidget(number);row.addWidget(box);self.metric_cards.append(number)
        v.addLayout(row);self.cards=label('');self.cards.hide();self.scope_banner=label('Fast Screening 用于低精度筛选和假设生成。生成分子不等于 binder，Q-score 不等于 affinity。');v.addWidget(self.scope_banner);self.warning_summary=label('暂无结果警告');v.addWidget(self.warning_summary);self.scope=QPlainTextEdit();self.scope.setReadOnly(True);self.scope.setMaximumHeight(120);v.addWidget(fold('科学解释边界 / 完整 Warnings',self.scope))
        row=QHBoxLayout();b=button('打开完整 HTML 报告',lambda:self.open_report('html'));b.setProperty('primary',True);row.addWidget(b);self.report_html_button=b;self.report_md_button=button('打开 Markdown 报告',lambda:self.open_report('md'));row.addWidget(self.report_md_button);row.addWidget(button('打开 Run 文件夹',lambda:self.open_local(self.loaded_run)));row.addStretch();v.addLayout(row)
        row=QHBoxLayout();self.mapping_status=label('Mapping data not available for this historical run');row.addWidget(self.mapping_status,1);self.mapping_button=button('Open mapping table',self.open_mapping_table);self.mapping_button.setEnabled(False);row.addWidget(self.mapping_button);v.addLayout(row)
        row=QHBoxLayout();self.structure_status=label('Structure Mode: historical adapter data unavailable');row.addWidget(self.structure_status,1);self.aggregate_qc_button=button('Open aggregate QC',lambda:self.open_aggregate_artifact('aggregate_qc.json'));self.repeat_mapping_button=button('Open repeat mapping',lambda:self.open_aggregate_artifact('repeat_chain_table.csv'));row.addWidget(self.aggregate_qc_button);row.addWidget(self.repeat_mapping_button);self.aggregate_qc_button.setEnabled(False);self.repeat_mapping_button.setEnabled(False);v.addLayout(row)
        self.result_tabs=QTabWidget();v.addWidget(self.result_tabs,1);metrics=QWidget();mv=QVBoxLayout(metrics);mv.setContentsMargins(0,4,0,0);self.metrics_empty=label('No targets selected — no molecule metrics available.');self.metrics_empty.hide();mv.addWidget(self.metrics_empty);self.summary_table=table(['Family','State','Generated','Valid Unique','ED Volume','Median Qnorm','Diversity','Scaffold Count']);self.summary_table.setEditTriggers(QAbstractItemView.NoEditTriggers);self.summary_table.setSelectionMode(QAbstractItemView.ExtendedSelection);mv.addWidget(self.summary_table);row=QHBoxLayout();row.addWidget(button('复制选中',self.copy_metrics));row.addWidget(button('导出当前显示 CSV',self.export_metrics));row.addStretch();mv.addLayout(row);self.result_tabs.addTab(metrics,'Metrics')
        self.gallery_scroll=QScrollArea();self.gallery_scroll.setWidgetResizable(True);self.gallery_widget=QWidget();self.gallery_layout=QGridLayout(self.gallery_widget);self.gallery_scroll.setWidget(self.gallery_widget);self.result_tabs.addTab(self.gallery_scroll,'Figures 图集');self.result_tabs.currentChanged.connect(lambda _:QTimer.singleShot(0,self.load_visible_thumbnails));self.gallery_scroll.verticalScrollBar().valueChanged.connect(self.load_visible_thumbnails)
        self.result_tabs.hide();v.addStretch(0)
    def load_results(self,run,automatic=False):
        if hasattr(self,'page_status'):self.page_status[4].setText('● LOADING · 正在读取结构化结果…')
        super().load_results(run,automatic)
    def show_results(self,r,automatic=False):
        if r.get('run_kind')=='structure_adaptation_stopped':
            self.result=r;self.loaded_run=r['run'];self.error_text='';self.report_html_button.setEnabled(False);self.report_md_button.setEnabled(False);self.result_header.setText('Structure adaptation stopped safely');self.history_badge.setText('Stopped safely — '+r['aggregate']['status']);self.result_empty.hide();self.result_tabs.hide();self.summary_table.setRowCount(0);self.mapping_status.setText('Residue mapping not applied');self.mapping_button.setEnabled(False);self.warning_summary.setText(r['aggregate'].get('reason',r['aggregate']['status']));self.scope.setPlainText('Structural adapter scope rejection. No pocket matching or chemical generation started.');self.update_structure_status(r);self.page_status[4].setText('! STOPPED · '+r['aggregate']['status']);self.page_status[3].setText('! Structure adaptation stopped safely');self.run_status.setText('Structure adaptation stopped safely');self.nav.setCurrentRow(4)
            for w in self.metric_cards:w.setText('—')
            self.update_nav();return
        self.result_tabs.show();self.summary_table.setSortingEnabled(False);super().show_results(r,automatic);s=r['summary'];k=s['key_metrics'];values=[len(s['selected_region_families']),len(s['targets']),k.get('generated','NA'),k.get('valid_unique_within_targets','NA'),k.get('physical_compatible_unique','NA'),len(s['warnings'])+len(r['warnings'])]
        self.update_structure_status(r);self.report_html_button.setEnabled(bool(r['reports'].get('html')));self.report_md_button.setEnabled(bool(r['reports'].get('md')))
        for w,value in zip(self.metric_cards,values):w.setText(str(value))
        no_targets=s.get('result_class')=='NO_TARGETS';self.metrics_empty.setVisible(no_targets);self.summary_table.setVisible(not no_targets)
        if no_targets:self.result_header.setText('Run complete — No targets selected')
        elif s.get('generation_status')=='COMPLETE' and s.get('generation_summary') and k.get('generated')==0:
            self.result_header.setText('Generation completed — 0 molecules generated')
        # A completed empty model output is not an execution error.
        self.summary_table.setColumnCount(9);self.summary_table.setHorizontalHeaderItem(8,QTableWidgetItem('Generation status'))
        statuses={(x['region_family_id'],x['state_id']):x for x in s.get('generation_summary',[])}
        for i in range(self.summary_table.rowCount()):
            key=(self.summary_table.item(i,0).text(),self.summary_table.item(i,1).text());row=statuses.get(key,{})
            value='Generation completed — 0 molecules generated' if row.get('generated')==0 else 'Generation completed'
            self.summary_table.setItem(i,8,QTableWidgetItem(value))
        mapping=r.get('mapping');self.mapping_button.setEnabled(bool(r.get('mapping_tables',{}).get('residue_mapping.csv')))
        if mapping:
            status='FAIL' if mapping.get('status') not in ['PASS','PASS_WITH_GAPS'] else ('WARN' if mapping.get('warnings') else 'PASS')
            self.mapping_status.setText('Residue Mapping · '+status+' · '+str(mapping.get('mapping_mode','unknown'))+' · '+str(mapping.get('mapped_chains',len(mapping.get('chain_mappings',[]))))+' chains');self.mapping_status.setToolTip(json.dumps(mapping,ensure_ascii=False,indent=2))
        else:self.mapping_status.setText('Mapping data not available for this historical run');self.mapping_status.setToolTip('')
        self.result_empty.hide();self.history_badge.setText('✓ Current Run — Completed' if automatic else 'Historical Run — Read Only');warnings=s['warnings']+r['warnings'];self.warning_summary.setText(('! '+str(len(warnings))+' warnings · '+warnings[0][:160]) if warnings else '✓ 无额外警告');self.warning_summary.setToolTip('\n'.join(warnings));self.page_status[4].setText(('! WARN' if warnings else '✓ PASS')+' · 结果已加载');self.view_results_button.show()
        for i in range(self.summary_table.rowCount()):
            for j in range(self.summary_table.columnCount()):self.summary_table.setItem(i,j,NumericItem(self.summary_table.item(i,j).text()))
        self.summary_table.setSortingEnabled(True);self.summary_table.horizontalHeader().setMinimumSectionSize(88);self.update_nav()
    def build_gallery(self,figures):
        self.thumbnail_queue=[];self.thumbnails_loaded=0
        while self.gallery_layout.count():
            item=self.gallery_layout.takeAt(0)
            if item.widget():item.widget().deleteLater()
        if not figures:self.gallery_layout.addWidget(label('No figures available — no chemical-space figures are created for runs without targets.'),0,0)
        for i,f in enumerate(figures):
            box,v=card(f['name'].replace('_',' '));box.setMinimumWidth(260);preview=button('点击查看大图',lambda checked=False,p=f['path']:self.open_figure(p));preview.setMinimumHeight(180);preview.setIconSize(QSize(360,180));v.addWidget(preview);v.addWidget(label('PNG · 保持原始比例'));row=QHBoxLayout()
            for ext in ['csv','svg','pdf']:
                b=button(ext.upper(),lambda checked=False,p=f['related'].get(ext):self.open_local(p));b.setEnabled(ext in f['related']);row.addWidget(b)
            v.addLayout(row);v.addWidget(button('所在文件夹',lambda checked=False,p=str(Path(f['path']).parent):self.open_local(p)));self.gallery_layout.addWidget(box,i//2,i%2);self.thumbnail_queue.append((preview,f['path']))
        QTimer.singleShot(0,self.load_visible_thumbnails)
    def open_mapping_table(self):
        path=(self.result or {}).get('mapping_tables',{}).get('residue_mapping.csv')
        if path:self.open_local(path)
    def update_structure_status(self,r):
        a=r.get('aggregate');tables=r.get('aggregate_tables',{});self.aggregate_qc_button.setEnabled(bool(tables.get('aggregate_qc.json')));self.repeat_mapping_button.setEnabled(bool(tables.get('repeat_chain_table.csv')))
        if not a:self.structure_status.setText('Structure Mode: historical adapter data unavailable');self.structure_status.setToolTip('');return
        mode=a.get('structure_mode');text={'conventional':'Conventional','repeat_aggregate':'Repeat Aggregate','unsupported_aggregate':'Unsupported Aggregate'}.get(mode,str(mode));details=a.get('adapters',[a]);details=details[0] if details else a
        self.structure_status.setText('Structure Mode: '+text+' · '+a.get('status','')+(f" · Copies {details.get('copy_count')} · Central {details.get('central_original_chain')} · Window ±{details.get('window_radius')}" if mode=='repeat_aggregate' else ''));self.structure_status.setToolTip(json.dumps(a,ensure_ascii=False,indent=2))
    def open_aggregate_artifact(self,name):
        path=(self.result or {}).get('aggregate_tables',{}).get(name)
        if path:self.open_local(path)
    def load_visible_thumbnails(self,*_):
        if not hasattr(self,'gallery_scroll') or not self.gallery_scroll.isVisible():return
        remaining=[];viewport=self.gallery_scroll.viewport()
        for widget,path in self.thumbnail_queue:
            rect=widget.rect();rect.moveTopLeft(widget.mapTo(viewport,rect.topLeft()))
            if not rect.intersects(viewport.rect()):remaining.append((widget,path));continue
            def thumb(p=path):
                reader=QImageReader(p);reader.setScaledSize(reader.size().scaled(QSize(360,180),Qt.KeepAspectRatio));return reader.read()
            def loaded(img,w=widget):
                try:
                    if img.isNull():w.setText('! 图像缺失 / 无法读取')
                    else:w.setIcon(QIcon(QPixmap.fromImage(img)));w.setText('');self.thumbnails_loaded+=1
                except RuntimeError:pass  # a historical result may have been replaced while reading
            self.worker(thumb,loaded)
        self.thumbnail_queue=remaining
    def open_figure(self,path):
        if not Path(path).is_file():return self.fail('figure missing: '+path)
        self.figure_viewer=FigureViewer(path,self);self.figure_viewer.show()
    def metric_text(self,selected=False):
        out=io.StringIO();writer=csv.writer(out,delimiter='\t' if selected else ',');writer.writerow([self.summary_table.horizontalHeaderItem(j).text() for j in range(self.summary_table.columnCount())]);rows=sorted({x.row() for x in self.summary_table.selectedIndexes()}) if selected else range(self.summary_table.rowCount())
        for i in rows:writer.writerow([self.summary_table.item(i,j).text() for j in range(self.summary_table.columnCount())])
        return out.getvalue()
    def copy_metrics(self):QApplication.clipboard().setText(self.metric_text(True))
    def export_metrics(self):
        folder=ROOT/'10_ROUNDS'/ROUND/'02_OUTPUTS';path,_=QFileDialog.getSaveFileName(self,'导出当前显示 CSV',str(folder/('metrics_'+time.strftime('%Y%m%d_%H%M%S')+'.csv')),'CSV (*.csv)')
        if path:
            from .storage import guard
            try:
                p=guard(path,folder)
                with p.open('x',encoding='utf-8-sig',newline='') as f:f.write(self.metric_text())
                self.statusBar().showMessage('已导出显示数据：'+str(p))
            except Exception as e:self.fail(str(e))
    def build_settings(self):
        v=self.page();self.setting_fields={};grid=QGridLayout();v.addLayout(grid)
        for col,(title,fields) in enumerate([('Backend',[('distro','WSL distro'),('launcher','Backend command')]),('Paths',[('root','Canonical root'),('project_parent','Project parent')])]):
            box,bv=card(title);f=QFormLayout()
            for key,text in fields:
                w=QLineEdit(self.settings[key]);w.setToolTip(self.settings[key]);self.setting_fields[key]=w;f.addRow(text,w)
                if key=='root':w.setReadOnly(True)
            bv.addLayout(f);grid.addWidget(box,0,col)
        box,bv=card('Appearance');self.theme=QComboBox();self.theme.addItems(['System','Light','Dark']);self.theme.setCurrentText(self.settings['theme']);bv.addWidget(self.theme);grid.addWidget(box,1,0);box,bv=card('Behavior');self.open_after=QCheckBox('运行完成后打开 HTML 报告');self.open_after.setChecked(self.settings['open_report']);self.remember=QCheckBox('Remember last project');self.remember.setChecked(self.settings.get('remember_project',False));bv.addWidget(self.open_after);bv.addWidget(self.remember);grid.addWidget(box,1,1)
        row=QHBoxLayout()
        for text,fn in [('保存设置',self.save_preferences),('重新发现 WSL',self.discover),('Backend Doctor',self.doctor)]:row.addWidget(button(text,fn))
        row.addStretch();v.addLayout(row);self.backend_label=label('正在检查 WSL…');v.addWidget(self.backend_label);self.doctor_table=table(['检查项','状态']);self.doctor_table.setEditTriggers(QAbstractItemView.NoEditTriggers);v.addWidget(self.doctor_table,1);self.doctor_detail=QPlainTextEdit();self.doctor_detail.setReadOnly(True);self.doctor_detail.setMaximumHeight(110);v.addWidget(fold('Doctor details / 失败原因',self.doctor_detail));self.about=label('PathPocket Fast Screening Baseline 1.0\nGUI v0.1.6 (portable transport) · Backend v0.3.0\nEngine 09f133da913179f82b285dbb046f1ecb81d1da37\n低精度筛选与假设生成 · 无 telemetry\n用户项目目录: '+str(ROOT));v.addWidget(self.about)
    def save_preferences(self):
        self.settings['remember_project']=self.remember.isChecked();super().save_preferences()
