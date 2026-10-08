"""Integrated v1.0.6 presentation frontend; frozen CLI owns all science."""
import os,sys,json,csv,shutil,datetime,uuid,io
from pathlib import Path
import yaml
from PySide6.QtCore import Qt,QTimer,QProcess,QUrl
from PySide6.QtGui import QPixmap,QFontDatabase,QFont,QShortcut,QKeySequence
from PySide6.QtWidgets import QApplication,QMainWindow,QWidget,QVBoxLayout,QHBoxLayout,QFormLayout,QLabel,QLineEdit,QPushButton,QListWidget,QStackedWidget,QTabWidget,QTableWidget,QTableWidgetItem,QHeaderView,QAbstractItemView,QComboBox,QCheckBox,QFileDialog,QMessageBox,QInputDialog,QPlainTextEdit,QDialog,QScrollArea,QGridLayout,QSpinBox,QGroupBox,QProgressBar
from PySide6.QtSvgWidgets import QSvgWidget
from . import storage
from .bridge import Bridge
from .portable_projects import hydrate,unresolved,copy_demo,failure_stage,verified_no_targets_fixture,ENGINEERING_FIXTURE_FILE
from .ux_i18n import tr,language,display,limitations,figure_title,install_qt_language
from .ux_paths import ProjectPathResolver,read_preferences,save_preferences,preferred_workspace,default_workspace
from .ux_results import ResultIndex,FIELDS,write_index,truth,rows
from .ux_reports import reports
from .ux_progress import STAGES,snapshot
from .ux_guidance import MODES,DEMO_MODES,DEMO_PURPOSE,describe,infer,input_scaffold
from .ux_scene import scene
from .ux_structure import StructureDialog
from .ux_export import friendly,write_molecules,export_complex
from .ux_plots import HorizontalPlots,StoredPlot,HELP,plot_data

class NumericItem(QTableWidgetItem):
    def __lt__(self,other):
        try:return float(self.data(Qt.UserRole) or self.text())<float(other.data(Qt.UserRole) or other.text())
        except ValueError:return self.text()<other.text()

class Window(QMainWindow):
    def __init__(self,settings=None):
        super().__init__();self.prefs=read_preferences();self.mode=self.prefs['language'];self.paths=ProjectPathResolver();self.project=None;self.data=None;self.index=None;self.loaded_run=None;self.task='';self.error_text='';self.failure_code=None;self.project_validated=False;self.bound=[];self.translated_tabs=[];self.presentation=None;self.draw_process=None;self.pending_run=False;self.session=None
        install_qt_language(QApplication.instance(),self.mode)
        if os.name!='nt':
            font=Path(os.environ.get('PATHPOCKET_FRONTEND_BUNDLE',''))/'assets/NotoSansCJK-Regular.ttc'
            if font.exists():QFontDatabase.addApplicationFont(str(font));QApplication.instance().setFont(QFont('Noto Sans CJK SC',10))
        self.settings=settings or storage.default_settings();self.set_workspace(preferred_workspace(self.prefs),check=False)
        self.bridge=Bridge(self.settings,self);self.bridge.completed.connect(self.on_complete)
        self.setWindowTitle('PathPocket v1.0.6');self.resize(1200,800);self.setMinimumSize(920,620)
        base=QWidget();self.setCentralWidget(base);v=QVBoxLayout(base);top=QHBoxLayout();top.addWidget(QLabel('PathPocket  v1.0.6'));self.lang_combo=QComboBox();top.addStretch();top.addWidget(self.lang_combo);v.addLayout(top)
        for k in ['system','zh','en']:self.lang_combo.addItem(self.t(k),k)
        self.lang_combo.setCurrentIndex(self.lang_combo.findData(self.mode));self.lang_combo.currentIndexChanged.connect(self.change_language)
        self.scope=self.label('fast_value');v.addWidget(self.scope);body=QHBoxLayout();v.addLayout(body,1);self.nav=QListWidget();self.nav.setMaximumWidth(200);body.addWidget(self.nav);self.pages=QStackedWidget();body.addWidget(self.pages,1)
        for key in ['project','states','fast','run','results','settings']:self.nav.addItem(self.t(key))
        self.nav.currentRowChanged.connect(self.pages.setCurrentIndex)
        self.build_project();self.build_states();self.build_fast();self.build_run();self.build_results();self.build_settings();self.nav.setCurrentRow(0)
        self.timer=QTimer(self);self.timer.timeout.connect(self.tick);self.timer.start(700)
        self.setStyleSheet('QMainWindow{background:#f3f7f8} QLabel{color:#203b43} QPushButton{padding:7px 12px} QTabBar::tab{padding:9px 14px} QTableWidget{background:white} QListWidget{background:#e6f0f2;border:0} QListWidget::item{padding:14px} QListWidget::item:selected{background:#b9dbe1;color:#163941} QGroupBox{font-weight:600}');QTimer.singleShot(150,self.discover)
    def t(self,key,**kw):return tr(key,self.mode,**kw)
    def label(self,key):
        w=QLabel(self.t(key));w.setWordWrap(True);w.setTextInteractionFlags(Qt.TextSelectableByMouse);self.bound.append((w,key,'setText'));return w
    def button(self,key,fn):
        w=QPushButton(self.t(key));w.clicked.connect(fn);self.bound.append((w,key,'setText'));return w
    def page(self):
        w=QWidget();layout=QVBoxLayout(w);self.pages.addWidget(w);return layout
    def table(self,keys):
        w=QTableWidget(0,len(keys));w.setHorizontalHeaderLabels([self.t(k) for k in keys]);w.setProperty('headers',keys);w.setSelectionBehavior(QAbstractItemView.SelectRows);w.setEditTriggers(QAbstractItemView.NoEditTriggers);w.horizontalHeader().setSectionResizeMode(QHeaderView.Interactive);w.horizontalHeader().setStretchLastSection(True);return w
    def fill(self,table,rows):
        table.setSortingEnabled(False);table.setRowCount(len(rows))
        for i,row in enumerate(rows):
            for j,val in enumerate(row):
                item=NumericItem(display(val,self.mode));item.setToolTip(str(val));item.setData(Qt.UserRole,str(val));table.setItem(i,j,item)
        table.resizeColumnsToContents()
        for i in range(table.columnCount()):table.setColumnWidth(i,min(300,table.columnWidth(i)))
    def row(self,layout,items):
        row=QHBoxLayout()
        for item in items:row.addWidget(item)
        layout.addLayout(row)
    def build_project(self):
        v=self.page();self.workspace_text=QLineEdit(str(self.settings['root']));self.workspace_text.setReadOnly(True);self.row(v,[self.label('workspace'),self.workspace_text,self.button('browse',self.choose_workspace)])
        self.project_location=QLineEdit();self.project_location.setReadOnly(True);self.row(v,[self.label('project_folder'),self.project_location,self.button('open_folder',lambda:self.open_file(self.project)),self.button('copy_path',lambda:QApplication.clipboard().setText(self.project_location.text()))])
        self.row(v,[self.button('new',self.new_project),self.button('open_project',self.open_project_dialog),self.button('open_demo',self.open_demo_dialog),self.button('open_run',self.open_run_dialog)])
        self.mode_banner=QLabel();self.mode_banner.setWordWrap(True);self.mode_banner.setStyleSheet('background:#e1eef3;padding:14px');v.addWidget(self.mode_banner);self.update_guidance();self.storage_notice=self.label('drvfs');v.addWidget(self.storage_notice);v.addWidget(self.label('history'));self.history=self.table(['run','status','path']);self.history.cellDoubleClicked.connect(lambda r,c:self.load_results(self.history.item(r,2).text()));v.addWidget(self.history,1)
    def build_states(self):
        v=self.page();v.addWidget(self.label('input_note'));self.state_table=self.table(['state_id','state_label','inputs']);self.state_table.cellDoubleClicked.connect(self.edit_state);v.addWidget(self.state_table)
        self.row(v,[self.button('add_pdb',self.add_pdb),self.button('validate',self.validate_project)])
    def build_fast(self):
        v=self.page();f=QFormLayout();self.n=QSpinBox();self.n.setRange(1,10000);self.n.setValue(100);self.seed=QSpinBox();self.seed.setRange(0,2147483647);self.seed.setValue(42);self.iteration=QSpinBox();self.iteration.setRange(1,50);self.iteration.setValue(2)
        for k,w in [('molecules_per_target',self.n),('seed',self.seed),('iteration',self.iteration)]:f.addRow(self.label(k),w)
        v.addLayout(f);v.addWidget(self.label('yaml'));self.editor=QPlainTextEdit();self.editor.textChanged.connect(self.editor_changed);v.addWidget(self.editor,1);self.row(v,[self.button('save',self.save_config),self.button('validate',self.validate_project)])
        for spin in [self.n,self.seed,self.iteration]:spin.valueChanged.connect(self.invalidate)
    def build_run(self):
        v=self.page();self.run_status=self.label('idle');self.run_status.setStyleSheet('font-size:18px;font-weight:600');v.addWidget(self.run_status)
        self.run_mode=QLabel();self.run_mode.setWordWrap(True);v.addWidget(self.run_mode);self.run_context=QLabel();self.run_context.setWordWrap(True);v.addWidget(self.run_context)
        self.run_metrics=QLabel();self.run_metrics.setStyleSheet('background:#dcebf0;padding:12px;font-size:15px');self.run_metrics.setWordWrap(True);v.addWidget(self.run_metrics)
        self.run_location=QLineEdit();self.run_location.setReadOnly(True);self.row(v,[self.label('run_folder'),self.run_location]);self.run_button=self.button('start',self.run_clicked);self.run_button.setEnabled(False);self.stop_button=self.button('stop',lambda:self.bridge.stop());self.stop_button.setEnabled(False);self.folder_button=self.button('open_folder',lambda:self.open_file(self.loaded_run));self.folder_button.setEnabled(False)
        self.row(v,[self.button('doctor',self.discover),self.run_button,self.stop_button,self.folder_button,self.button('copy_path',lambda:QApplication.clipboard().setText(self.run_location.text()))])
        grid=QGridLayout();self.stage_cards={}
        for i,(key,zh,en) in enumerate(STAGES):
            card=QLabel();card.setMinimumHeight(56);card.setWordWrap(True);grid.addWidget(card,i//2,i%2);self.stage_cards[key]=card
        grid.setColumnStretch(0,1);grid.setColumnStretch(1,1);v.addLayout(grid)
        live=QCheckBox(self.t('live_log'));self.bound.append((live,'live_log','setText'));self.live_log=QPlainTextEdit();self.live_log.setReadOnly(True);self.live_log.setMaximumHeight(130);self.live_log.hide();live.toggled.connect(self.live_log.setVisible);v.addWidget(live);v.addWidget(self.live_log)
        self.log=QPlainTextEdit();self.log.setReadOnly(True);self.log.setMaximumHeight(120);self.log.hide();advanced=QCheckBox(self.t('advanced'));self.bound.append((advanced,'advanced','setText'));advanced.toggled.connect(self.log.setVisible);v.addWidget(advanced);v.addWidget(self.log);self.bridge.log.connect(self.log.appendPlainText);v.addStretch();self.render_progress()
    def render_progress(self):
        zh=language(self.mode)=='zh';snap=snapshot(self.loaded_run) if self.loaded_run else dict(requested=None,last={},events=[],stage='initialize',targets=[],done=[],generated=None,elapsed=None,complete=False,current_target=None)
        names={k:z if zh else e for k,z,e in STAGES};state=snap['stage'];elapsed=snap['elapsed'];clock=f'{elapsed//60:02d}:{elapsed%60:02d}' if elapsed is not None else '—'
        current=self.t('complete') if snap['complete'] else names.get(state,self.t('preflight'))
        if snap['complete']:self.run_status.setText(self.t('complete'))
        self.run_context.setText(self.t('current_stage')+': '+current+'  |  '+self.t('target')+': '+str(snap['current_target'] or self.t('waiting')))
        self.run_metrics.setText(self.t('target_progress')+f": {len(snap['done'])} / {len(snap['targets']) if snap['targets'] else '—'}   ·   "+self.t('written_molecules')+': '+str(snap['generated'] if snap['generated'] is not None else self.t('waiting'))+' / '+str(snap['requested'] if snap['requested'] is not None else '—')+'   ·   '+self.t('elapsed')+': '+clock)
        for i,(key,z,e) in enumerate(STAGES):
            item=snap['last'].get(key,{});status=item.get('status','pending').upper()
            if key=='initialize' and len(snap['events'])>1:status='PASS'
            label=self.t('complete' if status=='PASS' else 'failed' if status=='FAIL' else 'running' if status=='RUNNING' else 'waiting');color='#dfefe7' if status=='PASS' else '#ffe2df' if status=='FAIL' else '#d9eaf7' if status=='RUNNING' else '#edf1f4'
            self.stage_cards[key].setText(f'{i+1:02d}   '+(z if zh else e)+'\n'+label);self.stage_cards[key].setStyleSheet('padding:8px 12px;border-radius:5px;background:'+color)
        lines=[str(e.get('timestamp',''))[11:19]+'  '+names.get(e.get('step'),self.t('complete') if e.get('step')=='complete' else self.t('preflight'))+' · '+self.t('complete' if e.get('status')=='PASS' else 'failed' if e.get('status')=='FAIL' else 'running') for e in snap['events']]
        self.live_log.setPlainText('\n'.join(lines));self.live_log.verticalScrollBar().setValue(self.live_log.verticalScrollBar().maximum())
    def build_results(self):
        v=self.page();v.addWidget(self.label('view_only'));self.result_tabs=QTabWidget();v.addWidget(self.result_tabs,1);self.result_layouts=[]
        for k in ['overview','regions','molecules','space','files']:
            w=QWidget();self.result_layouts.append(QVBoxLayout(w));self.result_tabs.addTab(w,self.t(k))
        ov,regions,molecules,space,files=self.result_layouts
        self.space_tabs=QTabWidget();space.addWidget(self.space_tabs);chart_page=QWidget();space=QVBoxLayout(chart_page);self.space_tabs.addTab(chart_page,self.t('charts'));summary_page=QWidget();sv=QVBoxLayout(summary_page);self.diversity_table=self.table(['target_id','region_family_id','state_id','unique','cluster_count','scaffold_count','within_state_diversity']);sv.addWidget(self.diversity_table);self.space_tabs.addTab(summary_page,self.t('summaries'))
        self.result_mode_note=QLabel();self.result_mode_note.setWordWrap(True);self.result_mode_note.setStyleSheet('background:#e1eef3;padding:10px');ov.addWidget(self.result_mode_note);self.overview=QLabel();self.overview.setWordWrap(True);self.overview.setTextInteractionFlags(Qt.TextSelectableByMouse);ov.addWidget(self.overview);self.row(ov,[self.button('render',self.prepare_presentation),self.button('report_zh',lambda:self.open_report('zh')),self.button('report_en',lambda:self.open_report('en'))]);self.presentation_location=QLineEdit();self.presentation_location.setReadOnly(True);ov.addWidget(self.presentation_location)
        self.row(ov,[self.label('report_folder'),self.button('open_folder',lambda:self.open_file(self.presentation or (self.index.run/'08_REPORT' if self.index else None))),self.button('copy_path',lambda:QApplication.clipboard().setText(self.presentation_location.text()))])
        self.scope_details=QPlainTextEdit();self.scope_details.setReadOnly(True);self.scope_details.setVisible(False);self.scope_details.setMaximumHeight(180);scope_toggle=QCheckBox(self.t('warnings'));self.bound.append((scope_toggle,'warnings','setText'));scope_toggle.toggled.connect(self.scope_details.setVisible);ov.addWidget(scope_toggle);ov.addWidget(self.scope_details);ov.addStretch()
        self.region_table=self.table(['target_id','region_family_id','state_id','state_label','source_pdb','detected_pocket','center','local_fit_RMSD','consensus_residues','predicted_ED_volume','median_Q_normalized','generated','valid_unique','physical_compatible','region']);regions.addWidget(self.region_table)
        self.row(regions,[self.button('view_molecules',self.region_molecules),self.button('locate_region',self.locate_region),self.button('open_target',lambda:self.region_file('')),self.button('open_receptor',lambda:self.region_file('receptor.pdb')),self.button('open_full',lambda:self.region_file('receptor_full.pdb')),self.button('copy_center',self.copy_center)])
        self.target_filter=QComboBox();self.state_filter=QComboBox();self.qc_filter=QComboBox();self.search=QLineEdit();self.search.setPlaceholderText(self.t('search'))
        for k in ['all','valid_unique','physical_compatible','clash']:self.qc_filter.addItem(self.t(k),k)
        self.row(molecules,[self.label('target'),self.target_filter,self.label('state'),self.state_filter,self.label('qc'),self.qc_filter,self.search])
        for w in [self.target_filter,self.state_filter,self.qc_filter]:w.currentIndexChanged.connect(self.apply_filter)
        self.search.textChanged.connect(self.apply_filter);self.mol_count=self.label('empty');molecules.addWidget(self.mol_count);self.mol_tabs=QTabWidget();molecules.addWidget(self.mol_tabs,1);self.gallery_scroll=QScrollArea();self.gallery_scroll.setWidgetResizable(True);self.mol_tabs.addTab(self.gallery_scroll,self.t('gallery'));self.mol_table=self.table(FIELDS);self.mol_table.setSortingEnabled(True);self.mol_table.cellDoubleClicked.connect(lambda r,c:self.detail(self.find_row(self.mol_table.item(r,0).text())));self.mol_tabs.addTab(self.mol_table,self.t('table'))
        self.row(molecules,[self.button('locate_molecule',self.locate_selected),self.button('open_sdf',self.open_selected_sdf),self.button('open_folder',self.open_selected_folder),self.button('export_complex',self.export_selected_complex)]);self.row(molecules,[self.button('copy',self.copy_rows),self.button('copy_smiles',self.copy_selected),self.button('export_csv',lambda:self.export_selected('csv')),self.button('export_sdf',lambda:self.export_selected('sdf'))]);self.copy_shortcut=QShortcut(QKeySequence.Copy,self.mol_table);self.copy_shortcut.setContext(Qt.WidgetWithChildrenShortcut);self.copy_shortcut.activated.connect(self.copy_rows)
        self.space_title=self.label('profile');space.addWidget(self.space_title);self.plot_target=QComboBox();self.row(space,[self.label('target'),self.plot_target]);self.plot_target.currentIndexChanged.connect(self.rebuild_plot_nav)
        navrow=QHBoxLayout();left=QPushButton('‹');right=QPushButton('›');self.plot_nav=HorizontalPlots();self.plot_nav.setFixedHeight(70);self.plot_nav.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff);left.clicked.connect(lambda:self.scroll_plots(-220));right.clicked.connect(lambda:self.scroll_plots(220));navrow.addWidget(left);navrow.addWidget(self.plot_nav,1);navrow.addWidget(right);space.addLayout(navrow);self.plot_left=left;self.plot_right=right
        self.plot_help=QLabel();self.plot_help.setWordWrap(True);space.addWidget(self.plot_help);self.stored_plot=StoredPlot();space.addWidget(self.stored_plot,1);self.figure_preview=QLabel();self.figure_preview.setAlignment(Qt.AlignCenter);space.addWidget(self.figure_preview,1)
        self.figure_list=QListWidget();self.figure_list.hide();self.active_plot='PCA';self.plot_buttons={}
        self.row(space,[self.button('view_molecules',self.figure_molecules),self.button('source_csv',self.figure_source)])
        self.file_table=self.table(['files','path']);files.addWidget(self.file_table);self.file_table.cellDoubleClicked.connect(lambda r,c:self.open_file(self.file_table.item(r,1).text()));self.provenance=QPlainTextEdit();self.provenance.setReadOnly(True);self.provenance.setVisible(False);adv=QCheckBox(self.t('advanced'));self.bound.append((adv,'advanced','setText'));adv.toggled.connect(self.provenance.setVisible);files.addWidget(adv);files.addWidget(self.provenance)
    def build_settings(self):
        v=self.page();v.addWidget(self.label('default_workspace'));self.default_path=QLineEdit(str(preferred_workspace(self.prefs)));self.row(v,[self.default_path,self.button('browse',self.pick_default)]);self.use_default=QCheckBox(self.t('use_default'));self.bound.append((self.use_default,'use_default','setText'));self.use_default.setChecked(self.prefs['use_default']);self.remember=QCheckBox(self.t('remember'));self.bound.append((self.remember,'remember','setText'));self.remember.setChecked(self.prefs['remember']);v.addWidget(self.use_default);v.addWidget(self.remember);self.row(v,[self.button('persist',self.persist),self.button('restore',lambda:self.default_path.setText(str(default_workspace())))]);help_toggle=QCheckBox(self.t('advanced'));help_body=self.label('scope');help_body.hide();help_toggle.toggled.connect(help_body.setVisible);v.addWidget(help_toggle);v.addWidget(help_body);v.addStretch()
    def change_language(self):
        self.mode=self.lang_combo.currentData();self.prefs['language']=self.mode;save_preferences(self.prefs)
        install_qt_language(QApplication.instance(),self.mode)
        for w,k,method in self.bound:
            try:getattr(w,method)(self.t(k))
            except RuntimeError:pass
        for i,k in enumerate(['project','states','fast','run','results','settings']):self.nav.item(i).setText(self.t(k))
        for i,k in enumerate(['overview','regions','molecules','space','files']):self.result_tabs.setTabText(i,self.t(k))
        for i,k in enumerate(['gallery','table']):self.mol_tabs.setTabText(i,self.t(k))
        for i,k in enumerate(['charts','summaries']):self.space_tabs.setTabText(i,self.t(k))
        for i in range(self.lang_combo.count()):self.lang_combo.setItemText(i,self.t(self.lang_combo.itemData(i)))
        for i in range(self.qc_filter.count()):self.qc_filter.setItemText(i,self.t(self.qc_filter.itemData(i)))
        for table in self.findChildren(QTableWidget):table.setHorizontalHeaderLabels([self.t(k) for k in table.property('headers') or []])
        self.search.setPlaceholderText(self.t('search'));self.run_status.setText(self.t('validated' if self.project_validated else 'idle'))
        if self.index:self.show_index(reset_filters=False)
        self.render_progress();self.update_guidance()
    def set_workspace(self,value,check=True):
        root=self.paths.native(value).expanduser().resolve()
        info=self.paths.preflight(root) if check else None
        root.mkdir(parents=True,exist_ok=True);storage.ROOT=root
        os.environ.update(PATHPOCKET_USER_HOME=str(root),PATHPOCKET_WORKSPACE=self.paths.backend(root))
        self.settings.update(root=str(root),project_parent=str(root/'20_PROJECTS'),work=str(root/'10_ROUNDS'/storage.ROUND/'01_WORK/gui_sessions'))
        if hasattr(self,'bridge'):self.bridge.settings=self.settings
        if hasattr(self,'workspace_text'):self.workspace_text.setText(str(root))
        if info and hasattr(self,'storage_notice'):self.storage_notice.setText(self.t('writable')+' · '+self.t('free')+f": {info['free_bytes']/1024**3:.1f} GB\n"+(self.t('low_disk') if info['free_bytes']<10*1024**3 else self.t('drvfs') if os.name=='nt' else ''))
        if self.prefs.get('remember'):self.prefs['last_project_directory']=str(root);save_preferences(self.prefs)
        return root
    def choose_workspace(self):
        if self.bridge.busy:return self.fail(self.t('busy'))
        p=QFileDialog.getExistingDirectory(self,self.t('workspace'),self.settings['root'])
        if p:
            try:self.set_workspace(p);self.project=None;self.data=None;self.invalidate();self.project_location.clear();self.fill(self.history,[])
            except Exception as e:self.fail(self.t(str(e)) if str(e) in ['protected','unwritable'] else str(e))
    def pick_default(self):
        p=QFileDialog.getExistingDirectory(self,self.t('default_workspace'),self.default_path.text())
        if p:self.default_path.setText(p)
    def persist(self):
        try:
            info=self.paths.preflight(self.default_path.text());self.prefs.update(default_workspace_windows=info['path'] if os.name=='nt' else self.prefs['default_workspace_windows'],default_workspace_linux=info['path'] if os.name!='nt' else self.prefs['default_workspace_linux'],default_workspace_wsl=info['backend'],use_default=self.use_default.isChecked(),remember=self.remember.isChecked());save_preferences(self.prefs)
        except Exception as e:self.fail(str(e))
    def new_project(self):
        if self.bridge.busy:return self.fail(self.t('busy'))
        dialog=QDialog(self);dialog.setWindowTitle(self.t('new'));dialog.resize(780,490);v=QVBoxLayout(dialog);mode_box=QComboBox();
        for key,values in MODES.items():mode_box.addItem(values[0 if language(self.mode)=='zh' else 1],key)
        explanation=QLabel();explanation.setWordWrap(True);mode_box.currentIndexChanged.connect(lambda:explanation.setText(describe(mode_box.currentData(),language(self.mode)=='zh')));explanation.setText(describe('single',language(self.mode)=='zh'));v.addWidget(self.label('analysis_mode'));v.addWidget(mode_box);v.addWidget(explanation);v.addWidget(self.label('mode_boundary'));
        name_edit=QLineEdit();root_edit=QLineEdit(str(preferred_workspace(self.prefs)));preview=QLabel();preview.setWordWrap(True)
        self.row(v,[QLabel(self.t('name')),name_edit]);choose=QPushButton(self.t('browse'))
        def browse():
            p=QFileDialog.getExistingDirectory(dialog,self.t('workspace'),root_edit.text())
            if p:root_edit.setText(p)
        choose.clicked.connect(browse);self.row(v,[QLabel(self.t('workspace')),root_edit,choose]);v.addWidget(QLabel(self.t('final_path')));v.addWidget(preview)
        def update():preview.setText(str(Path(root_edit.text())/'20_PROJECTS'/name_edit.text()))
        name_edit.textChanged.connect(update);root_edit.textChanged.connect(update);update();ok=QPushButton(self.t('ok'));cancel=QPushButton(self.t('cancel'));ok.clicked.connect(dialog.accept);cancel.clicked.connect(dialog.reject);self.row(v,[ok,cancel])
        if dialog.exec()!=QDialog.Accepted:return
        name=name_edit.text();root=root_edit.text()
        try:
            self.set_workspace(root);p=self.paths.project(root,name)
            if p.exists():raise ValueError(self.t('exists'))
            self.pending_mode=mode_box.currentData();self.pending_project=p;self.call('init',[self.paths.backend(p/'project.yml')],None,'init')
        except Exception as e:self.fail(str(e))
    def open_project_dialog(self):
        p,_=QFileDialog.getOpenFileName(self,self.t('open_project'),self.settings['root'],'YAML (*.yml *.yaml)')
        if p:self.open_project(p)
    def open_project(self,path,automatic=False):
        if self.bridge.busy:return self.fail(self.t('busy'))
        self.invalidate();self.error_text=''
        try:
            p=self.paths.native(path);p=p.parent if p.suffix in ['.yml','.yaml'] else p;root=self.paths.workspace(p);self.set_workspace(root);self.project=p;self.loaded_run=None;self.folder_button.setEnabled(False);data=yaml.safe_load((p/'project.yml').read_text(encoding='utf-8-sig'))
            if unresolved(data) and not automatic:
                box=QMessageBox(self);box.setWindowTitle('PathPocket');box.setText(self.t('hydrate'));yes=box.addButton(self.t('yes'),QMessageBox.YesRole);box.addButton(self.t('no'),QMessageBox.NoRole);box.setDefaultButton(yes);box.exec()
                if box.clickedButton()!=yes:self.invalidate();return
            data,_=hydrate(p);self.data=data;self.populate();self.validate_project()
        except Exception as e:self.fail(str(e))
    def open_demo_dialog(self):
        d=QDialog(self);d.setWindowTitle(self.t('open_demo'));d.resize(760,370);v=QVBoxLayout(d);combo=QComboBox()
        for key in DEMO_MODES:combo.addItem(key,key)
        note=QLabel();note.setWordWrap(True)
        def update():
            key=combo.currentData();zh=language(self.mode)=='zh';note.setText(describe(DEMO_MODES[key],zh)+'\n\n'+DEMO_PURPOSE[key][0 if zh else 1])
        combo.currentIndexChanged.connect(update);update();v.addWidget(combo);v.addWidget(note);ok=QPushButton(self.t('ok'));ok.clicked.connect(d.accept);v.addWidget(ok)
        if d.exec()!=QDialog.Accepted:return
        root=QFileDialog.getExistingDirectory(self,self.t('workspace'),str(preferred_workspace(self.prefs)))
        if root:self.open_demo(combo.currentData(),root)
    def open_demo(self,name,workspace=None,project_name=None):
        try:
            if self.bridge.busy:raise ValueError(self.t('busy'))
            self.set_workspace(workspace or self.settings['root']);p=copy_demo(Path(os.environ['PATHPOCKET_FRONTEND_BUNDLE'])/'payload/demos'/name,self.settings['root'],project_name);(p/'pathpocket_ui.json').write_text(json.dumps({'analysis_mode':DEMO_MODES.get(name,'single'),'demo':name,'presentation_only':True}),encoding='utf-8');self.open_project(p,True);return p
        except Exception as e:self.fail(str(e))
    def populate(self):
        self.project_location.setText(str(self.project));self.editor.blockSignals(True);self.editor.setPlainText(yaml.safe_dump(self.data,allow_unicode=True,sort_keys=False));self.editor.blockSignals(False);g=self.data.get('generation',{});self.n.setValue(g.get('molecules',100));self.seed.setValue(g.get('seed',42));self.iteration.setValue(g.get('iteration',2) if isinstance(g.get('iteration',2),int) else 2)
        self.fill(self.state_table,[[sid,s.get('label',sid),'\n'.join(s.get('structures',[]))] for sid,s in self.data.get('protein',{}).get('states',{}).items()]);self.refresh_history();self.update_guidance()
    def add_pdb(self):
        if not self.project:return self.fail(self.t('no_project'))
        sid,ok=QInputDialog.getItem(self,self.t('states'),self.t('state_id'),list(self.data.get('protein',{}).get('states',{})) or ['state_A'],0,True)
        if not ok:return
        files,_=QFileDialog.getOpenFileNames(self,self.t('add_pdb'),str(self.project),'Protein structures (*.pdb *.cif *.mmcif)')
        if not files:return
        try:
            storage.safe_name(sid);dest=self.project/'inputs';dest.mkdir(exist_ok=True);paths=[]
            for source in files:
                out=dest/(sid+'_'+uuid.uuid4().hex[:6]+'_'+Path(source).name);shutil.copy2(source,out);paths.append(self.paths.backend(out))
            self.data['protein']['states'][sid]=dict(label=sid,order=len(self.data['protein']['states']),structures=paths);self.populate();self.invalidate()
        except Exception as e:self.fail(str(e))
    def edit_state(self,row,column):
        if not self.data:return
        sid=self.state_table.item(row,0).text();old=self.state_table.item(row,column).text();value,ok=QInputDialog.getMultiLineText(self,self.t('states'),self.t(['state_id','state_label','inputs'][column]),old)
        if not ok:return
        try:
            d=storage.parse_yaml(self.editor.toPlainText());states=d['protein']['states']
            if column==0:
                storage.safe_name(value)
                if value!=sid and value in states:raise ValueError(self.t('exists'))
                states[value]=states.pop(sid)
            elif column==1:states[sid]['label']=value
            else:states[sid]['structures']=[self.paths.backend(p.strip()) for p in value.splitlines() if p.strip()]
            self.data=d;self.populate();self.invalidate()
        except Exception as e:self.fail(str(e))
    def invalidate(self,*_):self.project_validated=False;self.run_button.setEnabled(False) if hasattr(self,'run_button') else None
    def editor_changed(self):
        self.invalidate()
        try:
            g=storage.parse_yaml(self.editor.toPlainText()).get('generation',{})
            for key,widget in [('molecules',self.n),('seed',self.seed),('iteration',self.iteration)]:
                if isinstance(g.get(key),int):widget.blockSignals(True);widget.setValue(g[key]);widget.blockSignals(False)
        except Exception:pass
    def save_config(self):
        if not self.project:return self.fail(self.t('no_project'))
        try:
            d=storage.parse_yaml(self.editor.toPlainText());d.setdefault('generation',{}).update(molecules=self.n.value(),seed=self.seed.value(),iteration=self.iteration.value());d['project']['output_root']=self.paths.backend(self.project);history=self.project/'config_history';history.mkdir(exist_ok=True);shutil.copy2(self.project/'project.yml',history/('before_save_'+uuid.uuid4().hex+'.yml'));storage.atomic_text(self.project/'project.yml',storage.dump_yaml(d));self.data=d;self.validate_project()
        except Exception as e:self.fail(str(e))
    def validate_project(self):
        if not self.project:return self.fail(self.t('no_project'))
        try:
            d=storage.parse_yaml(self.editor.toPlainText())
            # Spin-box edits apply to existing fields; all other frozen schema values survive.
            d.setdefault('generation',{}).update(molecules=self.n.value(),seed=self.seed.value(),iteration=self.iteration.value())
            current=storage.parse_yaml((self.project/'project.yml').read_text(encoding='utf-8-sig'))
            if d!=current:
                h=self.project/'config_history';h.mkdir(exist_ok=True);shutil.copy2(self.project/'project.yml',h/('before_validate_'+uuid.uuid4().hex+'.yml'));storage.atomic_text(self.project/'project.yml',storage.dump_yaml(d));self.data=d
        except Exception as e:return self.fail(str(e))
        self.invalidate();self.call('validate',[self.paths.backend(self.project/'project.yml')],self.project,'validate')
    def discover(self):self.call('doctor',[],None,'doctor')
    def call(self,command,args,project,task):
        try:
            self.error_text='';self.task=task;self.session=self.bridge.start(command,args,project);self.run_status.setText(self.t('running'));self.stop_button.setEnabled(task=='run')
            for i in [0,1,2,5]:self.pages.widget(i).setEnabled(False)
        except Exception as e:self.fail(str(e))
    def run_clicked(self):
        if not self.project_validated:return self.fail(self.t('not_validated'))
        fixture=verified_no_targets_fixture(self.project);marker=self.project/ENGINEERING_FIXTURE_FILE
        if marker.exists() and not fixture:return self.fail('工程夹具标记无效 / Engineering fixture marker invalid')
        command='run-engineering-no-targets' if fixture else 'run';args=[self.paths.backend(self.project/'project.yml')]
        if fixture:args.append(self.paths.backend(marker))
        self.loaded_run=None;self.folder_button.setEnabled(False);self.run_button.setEnabled(False);self.call(command,args,self.project,'run');self.nav.setCurrentRow(3)
    def on_complete(self,result):
        self.stop_button.setEnabled(False)
        for i in [0,1,2,5]:self.pages.widget(i).setEnabled(True)
        if result.get('status')!='PASS':
            events=[]
            if result.get('run_path'):
                from .contracts import progress
                events=progress(self.paths.native(result['run_path'])/'progress.jsonl')
            self.failure_code=failure_stage(self.task,result.get('error',''),events,result.get('ed2mol_started',False),bool(result.get('run_path')));return self.fail(result.get('error',result.get('status','FAIL')))
        if self.task=='doctor':self.doctor_data=result.get('data',{});self.run_status.setText(self.t('idle'))
        elif self.task=='init':
            config_path=self.pending_project/'project.yml';config=storage.parse_yaml(config_path.read_text(encoding='utf-8-sig'));storage.atomic_text(config_path,storage.dump_yaml(input_scaffold(config,getattr(self,'pending_mode','single'))))
            (self.pending_project/'pathpocket_ui.json').write_text(json.dumps({'analysis_mode':getattr(self,'pending_mode','single'),'presentation_only':True}),encoding='utf-8');self.open_project(self.pending_project,True)
        elif self.task=='validate':self.data=storage.parse_yaml((self.project/'project.yml').read_text(encoding='utf-8-sig'));self.populate();self.project_validated=True;self.run_button.setEnabled(True);self.run_status.setText(self.t('validated'))
        elif self.task=='run':self.run_button.setEnabled(True);self.load_results(self.paths.native(result['run_path']));self.refresh_history()
    def fail(self,message):
        self.error_text=str(message);self.log.appendPlainText(str(message));self.run_status.setText(self.t(self.failure_code) if self.failure_code else self.t('failed'));self.failure_code=None
        for key in ['protected','unwritable','exists','no_project','busy','not_validated','no_selection']:
            if str(message) in [key,self.t(key)]:self.run_status.setText(self.t(key));self.storage_notice.setText(self.t(key))
        if not self.bridge.busy:
            for i in [0,1,2,5]:self.pages.widget(i).setEnabled(True)
    def tick(self):
        if self.session and self.bridge.busy and self.task=='run':
            try:
                state=storage.read_json(self.session/'state.json')
                if state.get('run_path'):
                    self.loaded_run=self.paths.native(state['run_path']);self.run_location.setText(str(self.loaded_run));self.folder_button.setEnabled(self.loaded_run.is_dir())
                self.render_progress()
            except (OSError,ValueError):pass
    def refresh_history(self):
        result=[]
        if self.project:
            for p in sorted((self.project/'runs').glob('RUN_*'),reverse=True):
                try:m=storage.read_json(p/'run_manifest.json');result.append([p.name,self.t('complete') if m.get('status')=='COMPLETE' else m.get('status'),str(p)])
                except (OSError,ValueError):pass
        self.fill(self.history,result)
    def open_run_dialog(self):
        path=QFileDialog.getExistingDirectory(self,self.t('open_run'),self.settings['root'])
        if path:self.load_results(path)
    def load_results(self,run):
        try:
            if self.draw_process and self.draw_process.state()!=QProcess.NotRunning:raise ValueError(self.t('busy'))
            self.error_text=''
            self.index=ResultIndex(self.paths.native(run));self.loaded_run=self.index.run;self.presentation=None;self.run_location.setText(str(self.loaded_run));self.folder_button.setEnabled(True);self.show_index();self._molecule_dir=None;self.run_status.setText(self.t('zero') if not self.index.summary.get('targets') else self.t('complete'));self.nav.setCurrentRow(4)
            self.presentation_location.setText(str(self.index.run/'08_REPORT'));self.render_progress();self.update_guidance()
            # Molecule cards are expected to show their read-only 2D depictions as
            # soon as a completed run is opened.  Keep the existing button as a
            # manual rebuild action, but do not require that extra click.
            QTimer.singleShot(0,self.prepare_result_presentation)
        except Exception as e:self.fail(str(e))
    def prepare_result_presentation(self):
        if self.index and self.index.rows and self.presentation is None:
            self.prepare_presentation()
    def show_index(self,reset_filters=True):
        s=self.index.summary;m=s.get('key_metrics',{});self.overview.setText('\n'.join([self.t('project')+': '+str(s.get('project')),self.t('status')+': '+self.t('complete'),self.t('project_folder')+': '+str(self.index.run.parent.parent),self.t('run_folder')+': '+str(self.index.run),self.t('states')+': '+str(len(s.get('states',{}))),self.t('family')+': '+str(len(s.get('selected_region_families',[]))),self.t('target')+': '+str(len(s.get('targets',[]))),self.t('generated')+': '+str(m.get('generated','NA')),self.t('valid_unique')+': '+str(m.get('valid_unique_within_targets','NA')),self.t('physical_compatible')+': '+str(m.get('physical_compatible_unique','NA')),self.t('warnings')+': '+str(len(s.get('warnings',[]))),self.t('fast_value')]))
        summary={x['target_id']:x for x in s.get('generation_summary',[])};rr=[]
        try:imported=bool(yaml.safe_load((self.index.run/'00_INPUTS/project.yml').read_text()).get('region_discovery',{}).get('imported_manifest'))
        except (OSError,ValueError):imported=False
        families={f['region_family_id']:f for f in s.get('selected_region_families',[])}
        for target in self.index.targets:
            tid=target['target_id'];g=summary.get(tid,{});state=s.get('states',{}).get(target['state_id'],{});family=families.get(target.get('region_family_id'),{});rr.append([tid,target.get('region_family_id'),target.get('state_id'),state.get('label'),state.get('metadata',{}).get('pdb_id'),target.get('detected_pocket'),target.get('center'),target.get('local_fit_RMSD_A'),target.get('consensus_residues',family.get('consensus_residues')),g.get('predicted_ED_volume'),g.get('median_Q_normalized'),g.get('generated'),g.get('unique'),g.get('physical_compatible'),self.t('benchmark' if imported else 'region')])
        self.fill(self.region_table,rr)
        for combo,key in [(self.target_filter,'target_id'),(self.state_filter,'state_id')]:
            chosen=combo.currentData() if not reset_filters else '';combo.blockSignals(True);combo.clear();combo.addItem(self.t('all'),'')
            for value in sorted({r[key] for r in self.index.rows}):combo.addItem(value,value)
            combo.setCurrentIndex(max(0,combo.findData(chosen)));combo.blockSignals(False)
        self.apply_filter();self.space_title.setText(self.t('profile' if len(self.index.targets)<=1 else 'comparison'));self.figure_list.clear()
        for f in self.index.figures:
            name=f.get('name','');members=self.index.figure_members(f);self.figure_list.addItem(figure_title(name,self.mode)+' · '+self.t('contains',n=len(members) if members else 'NA'));item=self.figure_list.item(self.figure_list.count()-1);item.setData(Qt.UserRole,str(self.index.run/'08_REPORT'/f['path']))
        if self.figure_list.count():self.figure_list.setCurrentRow(0)
        self.fill(self.diversity_table,[[r.get(k) for k in self.diversity_table.property('headers')] for r in rows(self.index.run/'07_ANALYSIS/diversity.csv')])
        try:config=storage.parse_yaml((self.index.run/'00_INPUTS/project.yml').read_text(encoding='utf-8-sig'))
        except (OSError,ValueError):config={}
        self.scope_details.setPlainText('\n\n'.join(limitations(s,self.mode)));self.provenance.setPlainText(json.dumps(dict(manifest=self.index.manifest,configuration=config,targets=self.index.targets,warnings=s.get('warnings'),limitations=s.get('limitations'),source_sha256=self.index.source_hashes),ensure_ascii=False,indent=2));self.show_files();self.refresh_plot_targets()
    def show_files(self):
        pairs=[]
        for a in self.index.artifacts:
            p=self.index.safe(a['path']);pairs.append([Path(a['path']).name,str(p)])
        for p in [self.index.run/'run_manifest.json',self.index.run/'artifacts.json',self.index.run/'progress.jsonl',self.index.run.parent.parent/'project.yml']:pairs.append([p.name,str(p)])
        if self.presentation:pairs.extend([[self.t('report_'+lang),str(self.presentation/('report_'+lang+'.html'))] for lang in ['zh','en']])
        self.fill(self.file_table,pairs)
    def apply_filter(self,*_):
        if not self.index:return
        self.filtered=self.index.filtered(self.target_filter.currentData() or '',self.state_filter.currentData() or '',self.qc_filter.currentData() or 'all',self.search.text());self.mol_count.setText(self.t('contains',n=len(self.filtered)));self.fill(self.mol_table,[[r.get(k) for k in FIELDS] for r in self.filtered]);self.mol_table.setSortingEnabled(True)
        for col,key in enumerate(FIELDS):self.mol_table.horizontalHeaderItem(col).setToolTip(HELP.get('Qnorm' if key=='Q_total_normalized' else key,('',''))[0 if language(self.mode)=='zh' else 1])
        grid=QWidget();layout=QGridLayout(grid)
        for i,row in enumerate(self.filtered):
            card=QGroupBox(Path(friendly(self.index,row)).stem);cv=QVBoxLayout(card);svg=self.presentation/'thumbnails'/(row['_thumb']+'.svg') if self.presentation else None
            if svg and svg.exists():image=QSvgWidget(str(svg));image.setFixedSize(240,176);cv.addWidget(image)
            else:cv.addWidget(QLabel(self.t('render')))
            text=QLabel(row['target_id']+'\n'+self.t('physical_compatible' if truth(row.get('physical_compatible')) else 'clash' if truth(row.get('protein_clash')) or truth(row.get('internal_clash')) else 'qc')+'\n'+'\n'.join(self.t(k)+': '+display(row.get(k),self.mode) for k in ['Q_total_normalized','MW','cLogP','TPSA']));text.setWordWrap(True);cv.addWidget(text);b=QPushButton(self.t('detail'));b.clicked.connect(lambda checked=False,r=row:self.detail(r));cv.addWidget(b);loc=QPushButton(self.t('locate_molecule'));loc.clicked.connect(lambda checked=False,r=row:self.locate_structure(r['target_id'],r));cv.addWidget(loc);layout.addWidget(card,i//3,i%3)
        layout.setRowStretch((len(self.filtered)+2)//3,1);old=self.gallery_scroll.takeWidget();self.gallery_scroll.setWidget(grid)
        if old:old.deleteLater()
    def find_row(self,molecule_id):return next(r for r in self.index.rows if r['molecule_id']==molecule_id)
    def selected(self):return [self.find_row(self.mol_table.item(i.row(),0).text()) for i in self.mol_table.selectionModel().selectedRows()]
    def copy_selected(self):QApplication.clipboard().setText('\n'.join(r.get('smiles','') for r in self.selected()))
    def copy_rows(self):
        selected=self.selected()
        if not selected:return self.fail(self.t('no_selection'))
        stream=io.StringIO();writer=csv.DictWriter(stream,fieldnames=FIELDS+['smiles'],extrasaction='ignore',delimiter='\t');writer.writeheader();writer.writerows(selected);QApplication.clipboard().setText(stream.getvalue())
    def result_project(self):
        if self.index.run.parent.name=='runs' and self.index.run.parent.parent.parent.name=='20_PROJECTS':
            project=self.index.run.parent.parent;self.paths.preflight(self.paths.workspace(project));return project
        return Path(self.settings['root'])/'20_PROJECTS'/('REPLAY_'+self.index.run.name)
    def export_selected(self,kind,selection=None):
        chosen=selection if selection is not None else self.selected()
        if not chosen:return self.fail(self.t('no_selection'))
        try:folder=self.result_project()/'exports';folder.mkdir(parents=True,exist_ok=True)
        except Exception as e:return self.fail(str(e))
        p,_=QFileDialog.getSaveFileName(self,self.t('export_'+kind),str(folder/(friendly(self.index,chosen[0]) if kind=='sdf' and len(chosen)==1 else 'selected_'+uuid.uuid4().hex[:6]+'.'+kind)),kind.upper()+' (*.'+kind+')')
        if p:
            try:getattr(self.index,'export_'+kind)(chosen,p);self.run_status.setText(self.t('exported'))
            except Exception as e:self.fail(str(e))
    def detail(self,row):
        d=QDialog(self);d.setWindowTitle(self.t('detail'));d.resize(850,650);v=QVBoxLayout(d);view=QScrollArea();view.setWidgetResizable(True);inner=QWidget();f=QFormLayout(inner)
        if self.presentation:
            image=self.presentation/'thumbnails'/(row['_thumb']+'.svg')
            if image.exists():svg=QSvgWidget(str(image));svg.setFixedSize(240,176);v.addWidget(svg)
        for k in ['molecule_id','source_record','smiles']+[k for k in FIELDS if k!='molecule_id']+['ED_coverage_per_heavy_atom']:
            value=QLabel(display(row.get(k),self.mode));value.setWordWrap(True);value.setTextInteractionFlags(Qt.TextSelectableByMouse);value.setToolTip(HELP.get('Qnorm' if k=='Q_total_normalized' else k,('',''))[0 if language(self.mode)=='zh' else 1]);f.addRow(self.t(k),value)
        view.setWidget(inner);v.addWidget(view);self.row(v,[self.button('locate_molecule',lambda:self.locate_structure(row['target_id'],row)),self.button('open_sdf',lambda:self.open_file(self.molecule_file(row))),self.button('export_complex',lambda:self.export_complex_dialog(row))]);self.row(v,[self.button('copy_smiles',lambda:QApplication.clipboard().setText(row.get('smiles',''))),self.button('export_sdf',lambda:self.export_selected('sdf',[row])),self.button('raw_sdf',lambda:self.open_file(row['_raw_sdf'])),self.button('clean_sdf',lambda:self.open_file(row['_clean_sdf'])),self.button('open_target',lambda:self.open_file(row['_target_folder']))]);d.exec()
    def update_guidance(self):
        config=self.data or {};run=self.index.run if self.index and self.loaded_run==self.index.run else None;intent={}
        if run:
            try:config=storage.parse_yaml((run/'00_INPUTS/project.yml').read_text(encoding='utf-8-sig'))
            except (OSError,ValueError):pass
        elif self.project:
            try:intent=storage.read_json(self.project/'pathpocket_ui.json')
            except (OSError,ValueError):pass
        mode=intent.get('analysis_mode') or infer(config,run);text=describe(mode,language(self.mode)=='zh')
        if not run and config.get('protein',{}).get('states'):text+='\n'+self.t('input_mode_help')
        if intent.get('demo') in DEMO_PURPOSE:text+='\n'+DEMO_PURPOSE[intent['demo']][0 if language(self.mode)=='zh' else 1]
        if hasattr(self,'result_mode_note'):self.result_mode_note.setText(text+'\n'+self.t('journey'))
        if hasattr(self,'run_mode'):self.run_mode.setText(self.t('analysis_mode')+': '+MODES[mode][0 if language(self.mode)=='zh' else 1])
        if hasattr(self,'mode_banner'):self.mode_banner.setText(self.t('analysis_mode')+': '+text+'\n'+self.t('journey'))
    def locate_region(self):
        tid=self.selected_target()
        if tid:self.locate_structure(tid)
    def locate_selected(self):
        selected=self.selected()
        if not selected:return self.fail(self.t('no_selection'))
        self.locate_structure(selected[0]['target_id'],selected[0])
    def locate_structure(self,tid,row=None):
        try:
            data=scene(self.index,tid,row);data['friendly_filename']=friendly(self.index,row) if row else None;dialog=StructureDialog(data,language(self.mode)=='zh',self,on_export=(lambda:self.export_complex_dialog(row)) if row else None);self.structure_dialog=dialog;dialog.setAttribute(Qt.WA_DeleteOnClose);dialog.show();return dialog
        except Exception as e:self.fail(str(e))
    def selected_target(self):
        r=self.region_table.currentRow()
        return self.region_table.item(r,0).text() if r>=0 else None
    def region_molecules(self):
        tid=self.selected_target()
        if tid:self.target_filter.setCurrentIndex(self.target_filter.findData(tid));self.state_filter.setCurrentIndex(0);self.qc_filter.setCurrentIndex(0);self.search.clear();self.result_tabs.setCurrentIndex(2)
    def region_file(self,name):
        tid=self.selected_target()
        if tid:self.open_file(self.index.run/'06_CHEMICAL_CHALLENGE'/tid/name)
    def copy_center(self):
        tid=self.selected_target()
        if tid:QApplication.clipboard().setText(str(next(t for t in self.index.targets if t['target_id']==tid).get('center','NA')))
    def refresh_plot_targets(self):
        chosen=self.plot_target.currentData();self.plot_target.blockSignals(True);self.plot_target.clear()
        for t in self.index.targets:self.plot_target.addItem(t['target_id'],t['target_id'])
        self.plot_target.setCurrentIndex(max(0,self.plot_target.findData(chosen)));self.plot_target.blockSignals(False);self.rebuild_plot_nav()
    def scroll_plots(self,delta):
        bar=self.plot_nav.horizontalScrollBar();bar.setValue(bar.value()+delta)
    def rebuild_plot_nav(self,*_):
        if not self.index:return
        container=QWidget();layout=QHBoxLayout(container);self.plot_buttons={};self.extra_figures={}
        specs=['PCA','MW','cLogP','TPSA','Qnorm','SA','QED']
        for f in self.index.figures:
            if f['name'].startswith(('embedding_','descriptor_')) or f['name']=='normalized_Q':continue
            specs.append(f['name']);self.extra_figures[f['name']]=f
        for key in specs:
            button=QPushButton(key if key in HELP else figure_title(key,self.mode));button.setCheckable(True);button.setMinimumWidth(110);button.setStyleSheet('QPushButton:checked{background:#25798d;color:white;font-weight:600}');button.clicked.connect(lambda checked=False,k=key:self.choose_plot(k));layout.addWidget(button);self.plot_buttons[key]=button
        container.adjustSize();self.plot_nav.setWidget(container);self.choose_plot(self.active_plot if self.active_plot in specs else 'PCA')
    def choose_plot(self,key):
        self.active_plot=key
        for k,b in self.plot_buttons.items():b.setChecked(k==key)
        tid=self.plot_target.currentData();self.active_plot_data=None
        if not tid:return
        if key in HELP:
            data=plot_data(self.index,tid,key);self.active_plot_data=data;self.stored_plot.show();self.figure_preview.hide();self.stored_plot.show_data(data,language(self.mode)=='zh');self.plot_help.setText(HELP[key][0 if language(self.mode)=='zh' else 1]);self.active_source=Path(data['source'])
        else:
            f=self.extra_figures[key];self.stored_plot.hide();self.figure_preview.show();p=self.index.run/'08_REPORT'/f['path'];translated=self.presentation/'figures'/(key+'_'+language(self.mode)+'.png') if self.presentation else None
            if translated and translated.exists():p=translated
            pix=QPixmap(str(p));self.figure_preview.setPixmap(pix.scaled(900,430,Qt.KeepAspectRatio,Qt.SmoothTransformation));self.active_source=self.index.run/'08_REPORT'/f['source'];self.plot_help.setText(self.t('summary_plot_help'))
    def figure_molecules(self):
        tid=self.plot_target.currentData()
        if not tid:return
        self.target_filter.setCurrentIndex(self.target_filter.findData(tid));self.state_filter.setCurrentIndex(0);self.qc_filter.setCurrentIndex(1);self.search.clear();self.result_tabs.setCurrentIndex(2)
    def show_figure(self,i):
        if self.index and hasattr(self,'plot_target') and self.plot_target.count():self.choose_plot(self.active_plot)
    def figure_source(self):
        if getattr(self,'active_source',None):self.open_file(self.active_source)
    def molecule_file(self,row):
        if not getattr(self,'_molecule_dir',None):
            directory=self.result_project()/'presentation'/self.index.run.name/('FILES_'+uuid.uuid4().hex[:10])/'molecules';write_molecules(self.index,directory);self._molecule_dir=directory
        return self._molecule_dir/friendly(self.index,row)
    def open_selected_sdf(self):
        selected=self.selected()
        if selected:
            try:self.open_file(self.molecule_file(selected[0]))
            except Exception as e:self.fail(str(e))
    def open_selected_folder(self):
        selected=self.selected()
        if selected:
            try:self.open_file(self.molecule_file(selected[0]).parent)
            except Exception as e:self.fail(str(e))
    def export_selected_complex(self):
        selected=self.selected()
        if len(selected)!=1:return self.fail(self.t('select_one'))
        self.export_complex_dialog(selected[0])
    def export_complex_dialog(self,row):
        if row is None:return
        d=QDialog(self);d.setWindowTitle(self.t('export_complex'));v=QVBoxLayout(d);label=QLabel(self.t('target')+': '+row['target_id']+'\n'+self.t('molecule_id')+': '+Path(friendly(self.index,row)).stem+'\n\n'+self.t('complex_contents'));label.setWordWrap(True);v.addWidget(label);v.addWidget(self.label('complex_value'));location=QLineEdit(str(self.result_project()/'exports/complexes'));browse=QPushButton(self.t('browse'))
        def choose():
            path=QFileDialog.getExistingDirectory(d,self.t('export_complex'),location.text())
            if path:location.setText(path)
        browse.clicked.connect(choose);self.row(v,[location,browse]);go=QPushButton(self.t('export_complex'));go.clicked.connect(d.accept);self.row(v,[go])
        if d.exec()!=QDialog.Accepted:return
        try:
            dest=export_complex(self.index,row,location.text());self.last_complex_export=dest;self.run_status.setText(self.t('exported')+': '+str(dest));QMessageBox.information(self,self.t('exported'),str(dest))
        except Exception as e:self.fail(str(e))
    def open_file(self,path):
        if path:
            try:
                p=Path(path)
                if p.suffix.lower()=='.sdf' and not self.paths.has_default_application(p):
                    box=QMessageBox(self);box.setIcon(QMessageBox.Information);box.setWindowTitle(self.t('sdf_no_viewer_title'));box.setText(self.t('sdf_no_viewer'));box.setInformativeText(str(p))
                    choose=box.addButton(self.t('choose_program'),QMessageBox.ActionRole) if self.paths.can_choose_application() else None;folder=box.addButton(self.t('open_folder'),QMessageBox.ActionRole);copy=box.addButton(self.t('copy_path'),QMessageBox.ActionRole);box.addButton(QMessageBox.Cancel)
                    box.exec();clicked=box.clickedButton()
                    if choose is not None and clicked is choose:return self.paths.choose_application(p)
                    if clicked is folder:return self.paths.open(p.parent)
                    if clicked is copy:QApplication.clipboard().setText(self.paths.windows_target(p));return True
                    return False
                return self.paths.open(p)
            except Exception as e:
                detail=self.t('open_failed')+'\n'+str(path)+'\n'+str(e);self.log.appendPlainText(detail);self.run_status.setText(self.t('open_failed'));QMessageBox.warning(self,self.t('open_failed'),detail);return False
    def open_report(self,lang):
        if self.presentation:self.open_file(self.presentation/('report_'+lang+'.html'))
        else:self.prepare_presentation()
    def prepare_presentation(self,destination=None):
        if not self.index or self.draw_process and self.draw_process.state()!=QProcess.NotRunning:return
        try:
            root=Path(destination) if destination else self.result_project()/'presentation'/self.index.run.name/('VIEW_'+datetime.datetime.now().strftime('%Y%m%d_%H%M%S')+'_'+uuid.uuid4().hex[:6]);p=write_index(self.index,root);self.presentation=root;self.presentation_location.setText(str(root));self.run_status.setText(self.t('rendering'))
            helper=Path(__file__).with_name('ux_draw.py');python=os.environ['PATHPOCKET_RUNTIME_PYTHON'];args=[self.paths.backend(helper),self.paths.backend(p),self.paths.backend(root/'thumbnails')]
            if os.name=='nt':exe='wsl.exe';args=['-d',self.settings['distro'],'--exec','/usr/bin/env','PATHPOCKET_WORKSPACE='+self.paths.backend(self.settings['root']),python]+args
            else:exe=python
            self.draw_process=QProcess(self);self.draw_process.finished.connect(self.presentation_done);self.draw_process.start(exe,args)
        except Exception as e:self.fail(str(e))
    def presentation_done(self,code,*_):
        if code:return self.fail(bytes(self.draw_process.readAllStandardError()).decode('utf-8',errors='replace'))
        try:
            reports(self.index,self.presentation)
            if not self.index.unchanged():raise ValueError('Scientific input hash changed')
            self.apply_filter();self.show_files();self.show_figure(self.figure_list.currentRow());self.run_status.setText(self.t('complete'))
        except Exception as e:self.fail(str(e))

def main():
    import argparse
    parser=argparse.ArgumentParser();parser.add_argument('--demo',action='store_true');parser.add_argument('--project');args=parser.parse_args()
    app=QApplication.instance() or QApplication(sys.argv);w=Window();w.show()
    if args.demo or args.project:
        timer=QTimer(w)
        def ready():
            if not w.bridge.busy and hasattr(w,'doctor_data'):
                timer.stop()
                if args.demo:w.open_demo_dialog()
                else:w.open_project(args.project)
        timer.timeout.connect(ready);timer.start(250)
    return app.exec()
