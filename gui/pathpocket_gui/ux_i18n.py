"""All v1.0.4 user-facing vocabulary. Identifiers/raw provenance are not translated."""
import locale
import os
from pathlib import Path
_qt_translator=None


def install_qt_language(app,mode):
    global _qt_translator
    from PySide6.QtCore import QTranslator,QLibraryInfo,Qt
    app.setAttribute(Qt.AA_DontUseNativeDialogs,True)
    if _qt_translator:app.removeTranslator(_qt_translator)
    _qt_translator=None
    if language(mode)=='zh':
        candidates=[Path(os.environ.get('PATHPOCKET_FRONTEND_BUNDLE',''))/'assets/qtbase_zh_CN.qm',Path(QLibraryInfo.path(QLibraryInfo.TranslationsPath))/'qtbase_zh_CN.qm']
        for p in candidates:
            translator=QTranslator(app)
            if translator.load(str(p)):_qt_translator=translator;app.installTranslator(translator);break
TEXT={
'charts':('图表','Charts'),'summaries':('汇总','Summaries'),'cluster_count':('聚类数','Cluster count'),'scaffold_count':('骨架数','Scaffold count'),'within_state_diversity':('状态内多样性','Within-state diversity'),
'project':('项目','Project'),'states':('蛋白状态','Protein States'),'fast':('快速筛选设置','Fast Screening Settings'),'run':('运行','Run'),'results':('结果','Results'),'settings':('设置与关于','Settings & About'),
'overview':('概览','Overview'),'regions':('区域','Regions'),'molecules':('分子','Molecules'),'space':('化学空间','Chemical Space'),'files':('文件与复现','Files & Provenance'),
'language':('界面语言','Language'),'zh':('简体中文','Simplified Chinese'),'en':('英语','English'),'system':('跟随系统','Follow system'),
'scope':('低精度筛选与假设生成；生成分子不等于结合分子，Qnorm 不等于亲和力。','Low-precision screening and hypothesis generation. Generated molecules are not verified binders; Qnorm is not affinity.'),
'new':('新建项目','New project'),'open_project':('打开已有项目','Open project'),'open_demo':('打开示例','Open Demo'),'open_run':('只读打开历史运行','Open historical run (read-only)'),
'name':('项目名称','Project name'),'workspace':('项目保存位置','Project workspace'),'browse':('选择文件夹…','Choose folder…'),'final_path':('最终路径','Final path'),'project_folder':('项目目录','Project folder'),'run_folder':('运行目录','Run folder'),'report_folder':('报告目录','Report folder'),
'history':('运行历史','Run history'),'refresh':('刷新','Refresh'),'save':('保存并校验','Save and validate'),'validate':('校验','Validate'),'doctor':('环境检查','Backend doctor'),'stop':('停止','Stop'),'start':('开始运行','Run'),'load':('加载','Load'),
'default_workspace':('默认项目保存位置','Default workspace'),'use_default':('新建项目默认使用此位置','Use this location for new projects'),'remember':('记住上次使用的位置','Remember last location'),'restore':('恢复默认','Restore default'),'persist':('保存设置','Save preferences'),
'writable':('可写','Writable'),'free':('可用空间','Free space'),'low_disk':('可用空间不足 10 GB，请检查','Less than 10 GB free; check storage'),'drvfs':('Windows 本地目录便于查看和备份；WSL 原生目录在部分 I/O 场景可能更快。','Windows folders are convenient for browsing and backup; WSL native storage may be faster for some I/O workloads.'),
'protected':('该目录为系统、安装或冻结源码目录，不能作为项目工作区。','This is a system, installation or frozen source folder; choose a project workspace.'),'unwritable':('目录不可写，请检查权限。','Folder is not writable; check permissions.'),'invalid_project':('项目必须位于工作区的 20_PROJECTS 子目录中。','Project must be directly inside a workspace’s 20_PROJECTS folder.'),'exists':('目标已存在，不覆盖。','Destination already exists; no overwrite.'),'no_project':('请先新建或打开项目。','Create or open a project first.'),'busy':('请等待当前操作完成。','Wait for the current operation to finish.'),
'hydrate':('此项目来自便携版模板，需要连接本机 PathPocket 运行环境。是否自动配置？','This portable project needs the installed PathPocket runtime. Configure it automatically?'),'yes':('是','Yes'),'no':('否','No'),'cancel':('取消','Cancel'),'ok':('确定','OK'),
'validated':('校验通过，可以运行','Validation passed; ready to run'),'not_validated':('尚未通过校验','Not validated'),'complete':('运行完成','Run complete'),'zero':('运行完成 — 未选择目标','Run complete — No targets selected'),'running':('运行中','Running'),'failed':('操作失败；请查看高级诊断','Operation failed; see advanced diagnostics'),'stopped':('已停止','Stopped'),'idle':('就绪','Ready'),
'advanced':('高级信息（原始诊断与复现记录）','Advanced (raw diagnostics and provenance)'),'progress':('运行进度','Run progress'),'log':('技术日志','Technical log'),'yaml':('配置 YAML','Configuration YAML'),'inputs':('输入结构','Input structures'),'add_pdb':('添加 PDB','Add PDB'),'state_id':('状态标识','State ID'),'state_label':('状态标签','State label'),'input_note':('每个状态使用已有 PDB；配置由后端校验。','Use existing PDB files for each state; the backend validates configuration.'),
'count':('数量','Count'),'target':('目标','Target'),'state':('状态','State'),'family':('区域家族','Region family'),'source_pdb':('来源 PDB','Source PDB'),'detected_pocket':('检测口袋','Detected pocket'),'center':('中心坐标','Center'),'local_fit_RMSD':('局部拟合 RMSD','Local-fit RMSD'),'consensus_residues':('共识残基','Consensus residues'),'predicted_ED_volume':('预测 ED 体积','Predicted ED volume'),'median_Q_normalized':('中位 Qnorm','Median Qnorm'),
'generated':('生成分子','Generated molecules'),'valid_unique':('有效且唯一','Valid unique'),'physical_compatible':('物理兼容','Physical-compatible'),'clash':('存在碰撞标记','Clash flagged'),'warnings':('提示与限制','Warnings and limitations'),'benchmark':('导入的基准区域','Imported benchmark region'),'region':('区域','Region'),'view_molecules':('查看对应分子','View molecules'),'open_target':('打开目标文件夹','Open target folder'),'open_receptor':('打开受体 PDB','Open receptor PDB'),'open_full':('打开完整受体 PDB','Open full receptor PDB'),'copy_center':('复制中心坐标','Copy center'),
'all':('全部','All'),'qc':('QC 筛选','QC filter'),'search':('搜索分子 ID / SMILES','Search molecule ID / SMILES'),'gallery':('卡片视图','Gallery'),'table':('表格视图','Table'),'detail':('分子详情','Molecule detail'),'copy':('复制','Copy'),'copy_smiles':('复制 SMILES','Copy SMILES'),'export_csv':('导出所选 CSV','Export selected CSV'),'export_sdf':('导出所选 SDF','Export selected SDF'),'raw_sdf':('原始 SDF','Raw SDF'),'clean_sdf':('清理后 SDF','Clean SDF'),'source_csv':('来源 CSV','Source CSV'),'open_file':('打开文件','Open file'),'selected':('已选择','Selected'),'empty':('没有符合条件的记录','No matching records'),'missing':('文件不可用；请查看原始路径','File unavailable; see original path'),'na':('NA（原结果未提供）','NA (not provided by source)'),
'molecule_id':('分子 ID','Molecule ID'),'target_id':('目标','Target'),'region_family_id':('区域家族','Region family'),'source_record':('来源记录','Source record'),'smiles':('标准 SMILES','Canonical SMILES'),'valid':('有效','Valid'),'unique':('唯一','Unique'),'protein_clash':('蛋白碰撞','Protein clash'),'internal_clash':('内部分子碰撞','Internal clash'),'Q_total_raw':('Q 原始值','Q raw'),'Q_total_normalized':('Qnorm','Qnorm'),'ED_coverage':('ED 覆盖率','ED coverage'),'ED_coverage_per_heavy_atom':('每重原子 ED 覆盖率','ED coverage / heavy atom'),'MW':('分子量（MW）','MW'),'cLogP':('cLogP','cLogP'),'TPSA':('拓扑极性表面积（TPSA）','TPSA'),'HBD':('氢键供体（HBD）','HBD'),'HBA':('氢键受体（HBA）','HBA'),'rotatable_bonds':('可旋转键','Rotatable bonds'),'ring_count':('环数','Ring count'),'aromatic_ring_count':('芳香环数','Aromatic ring count'),'fractionCSP3':('fractionCSP3','fractionCSP3'),'formal_charge':('形式电荷','Formal charge'),'SA':('SA','SA'),'QED':('QED','QED'),'PAINS':('PAINS','PAINS'),'Brenk':('Brenk','Brenk'),'scaffold':('Murcko 骨架','Murcko scaffold'),'cluster_id':('Butina 聚类','Butina cluster'),
'profile':('化学空间概况','Chemical-space profile'),'comparison':('化学空间比较','Chemical-space comparison'),'contains':('包含 {n} 个分子','Contains {n} molecules'),'render':('生成二维展示与双语报告','Prepare 2D display and bilingual reports'),'rendering':('正在绘制二维展示；原始结果保持只读','Rendering 2D display; original results remain read-only'),'report_zh':('中文报告','Chinese report'),'report_en':('英文报告','English report'),'presentation':('展示文件目录','Presentation directory'),'view_only':('只读回放；所有展示文件另存，原科学结果不变。','Read-only replay. Presentation files are separate; scientific artifacts remain unchanged.'),'pose_scope':('ED2Mol 生成构象，不代表经过验证的结合姿势。','ED2Mol-generated pose; not a validated binding pose.'),'true':('是','Yes'),'false':('否','No'),'path':('路径','Path'),'status':('状态','Status'),'seed':('随机种子','Seed'),'molecules_per_target':('每个目标的分子数','Molecules per target'),'iteration':('生成轮数','Iteration'),'read_only':('只读','Read-only'),'exported':('导出完成','Export complete'),'no_selection':('请先选择分子','Select molecules first'),'open_folder':('打开文件夹','Open folder'),'copy_path':('复制路径','Copy path'),'replay':('历史回放','Historical replay'),
'sdf_no_viewer_title':('未找到 SDF 默认查看程序','No default SDF viewer'),'sdf_no_viewer':('SDF 文件有效，但当前系统尚未关联查看程序。可打开所在文件夹、复制路径；Windows + WSL2 还可直接选择程序。','The SDF file is valid, but this system has no default viewer. You can open its folder or copy the path; Windows + WSL2 can also choose an app.'),'choose_program':('选择程序…','Choose app…'),'open_failed':('无法打开文件','Could not open file'),
'01_VALIDATE':('结构检查','Structure QC'),'02_ALIGN':('结构对齐','Alignment'),'03_REGION_DISCOVERY':('区域发现','Region discovery'),'04_REGION_MATCHING':('区域匹配','Region matching'),'05_TARGET_SELECTION':('目标选择','Target selection'),'06_CHEMICAL_CHALLENGE':('ED2Mol 生成','ED2Mol generation'),'07_ANALYSIS':('结果分析','Analysis'),'08_REPORT':('报告','Report'),'09_QC':('输出检查','Output QC'),
'WORKSPACE_NOT_AUTHORIZED':('工作区未授权','Workspace not authorized'),'RUNTIME_NOT_RESOLVED':('运行环境尚未连接','Runtime not resolved'),'VALIDATION_FAIL':('前置校验失败','Validation failed'),'STRUCTURE_QC_FAIL':('结构检查失败','Structure QC failed'),'REGION_DISCOVERY_FAIL':('区域发现或匹配失败','Region discovery or matching failed'),'TARGET_SELECTION_FAIL':('目标选择失败','Target selection failed'),'ED2MOL_FAIL':('ED2Mol 生成失败','ED2Mol generation failed'),'CHEMICAL_CHALLENGE_PREFLIGHT_FAIL':('生成启动前检查失败','Generation preflight failed'),'ANALYSIS_QC_FAIL':('结果分析失败','Analysis failed'),'REPORT_QC_FAIL':('报告输出失败','Report output failed'),'RUN_PREFLIGHT_FAIL':('运行前检查失败','Run preflight failed'),
'report_title':('PathPocket 只读结果报告','PathPocket read-only result report'),'language_note':('本报告读取既有科学数据；未重新计算性质、QC 或生成结果。','This report reads existing scientific data; no descriptors, QC or generation were recomputed.'),'figure_note':('原始科学图保持不变，其原标签作为来源数据保留。','Original scientific figures are unchanged; their labels are retained as source data.'),'no_ranking':('全部分子；未新增科学排序或结合能力判断。','All molecules; no new scientific ranking or binding claims.'),
}
def language(mode):
    if mode in ('zh','en'):return mode
    try:
        from PySide6.QtCore import QLocale
        return 'zh' if QLocale.system().name().lower().startswith('zh') else 'en'
    except ImportError:pass
    try:return 'zh' if str(locale.getlocale()[0]).lower().startswith(('zh','chinese')) else 'en'
    except ValueError:return 'en'
def tr(key,mode='system',**values):return TEXT.get(key,(key,key))[0 if language(mode)=='zh' else 1].format(**values)
def display(value,mode):
    if value is None or value=='':return 'NA'
    if str(value).lower()=='true':return tr('true',mode)
    if str(value).lower()=='false':return tr('false',mode)
    text=str(value)
    try:
        if '.' in text or 'e-' in text.lower():return format(float(text),'.6g')
    except ValueError:pass
    return text

LIMITATIONS=[
('本结果用于低精度工作流筛选和假设生成，不用于单独证明病理口袋、结合常数、药物滞留或荧光机制。','本结果只用于低精度筛选和假设生成，不能单独证明病理口袋、结合常数、药物滞留或荧光机制。','These low-precision outputs support screening and hypotheses, not proof of pathological pockets, binding constants, drug retention or fluorescence mechanisms.'),
('fpocket region ≠ validated pocket; predicted ligand ED ≠ experimental electron density.','fpocket 区域不等于验证口袋；预测配体 ED 不等于实验电子密度。','fpocket regions are not validated pockets; predicted ligand ED is not experimental electron density.'),
('Generated molecule ≠ binder; Q-score ≠ binding affinity; geometry-compatible ≠ binder.','生成分子或几何兼容不代表结合；Q 不代表结合亲和力。','Generation or geometry compatibility does not prove binding; Q is not binding affinity.'),
('One representative/state is not ensemble thermodynamics; one seed does not exhaust chemical space.','每状态单个代表结构不代表系综热力学；单个种子不能穷尽化学空间。','One representative per state is not ensemble thermodynamics; one seed does not exhaust chemical space.'),
('Generated molecules are not biological independent replicates; no p-value analysis.','生成分子不是独立生物学重复；不进行 p 值分析。','Generated molecules are not independent biological replicates; no p-value analysis is performed.'),
('Basic geometry QC is not a full strain-energy or pose-validation assessment.','基础几何 QC 不是完整应变能或构象验证。','Basic geometry QC is not a full strain-energy or pose-validation assessment.'),
('Raw engineering isotope labels are retained; these are not a designed isotope-labelled compound series.','保留原始工程同位素标签；这些分子不是设计的同位素标记化合物系列。','Raw engineering isotope labels are retained; this is not a designed isotope-labelled compound series.'),
('Canonical sequence/chain mapping requires unique high-confidence correspondence; renamed homomers and low-confidence mappings fail safely. Canonical IDs are project-local observed-sequence identities.','规范序列与链映射要求唯一高置信度对应；同源多聚体歧义和低置信度映射安全失败。规范 ID 只在项目内表示观测序列身份。','Canonical sequence/chain mapping requires unique high-confidence correspondence; ambiguous homomers and low-confidence mappings fail safely. Canonical IDs identify observed sequences within the project.'),
('No strict state-stable control; persistent/remodeling comparators must not be called proven stable controls.','没有严格状态稳定对照；持续或重塑比较区域不能称为已证实稳定的对照。','There is no strict state-stable control; persistent/remodeling comparators are not proven stable controls.')]
def limitations(summary,mode):
    mapping={source:(zh,en) for source,zh,en in LIMITATIONS}
    return [mapping[x][0 if language(mode)=='zh' else 1] if x in mapping else (('来源另有警告，请查看高级原始信息。' if language(mode)=='zh' else 'Additional source warning; see advanced original details.')) for x in summary.get('limitations',[])+summary.get('warnings',[])]

def figure_title(name,mode):
    mapping={'region_occurrence':('区域出现比例','Region occurrence'),'generation_unique':('有效唯一分子数','Valid unique molecules'),'generation_valid':('有效分子数','Valid molecules'),'predicted_ED':('预测 ED 体积','Predicted ED volume'),'normalized_Q':('标准化 Q','Normalized Q')}
    if name.startswith('embedding_'):return ('PCA 投影 · ' if language(mode)=='zh' else 'PCA projection · ')+name.removeprefix('embedding_')
    if name.startswith('descriptor_'):return name.removeprefix('descriptor_')
    return mapping.get(name,(name,name))[0 if language(mode)=='zh' else 1]

TEXT.update({'analysis_mode': ('分析模式', 'Analysis mode'), 'mode_boundary': ('此选择记录用途，不改变科学参数。请导入对应结构并通过既有 backend 验证；不会自动运行 MD 或绕过重复结构检查。', 'This selection records intent, not scientific parameters. Import appropriate structures and pass existing backend validation; no MD execution or repeat-gate bypass.'), 'journey': ('结构输入 → 分析模式 → 候选区域与对应关系 → 结构位置 → 区域专属生成分子 → 后续 docking / MD / 实验验证', 'Structure input → analysis mode → candidate regions and correspondence → structural location → target-specific generated molecules → downstream docking / MD / experiments'), 'live_log': ('实时阶段日志', 'Live stage log'), 'current_stage': ('当前阶段', 'Current stage'), 'target_progress': ('已完成目标', 'Completed targets'), 'written_molecules': ('已写出分子（非实时生成比例）', 'Written molecules (not live generation percentage)'), 'elapsed': ('已用时间', 'Elapsed time'), 'waiting': ('等待结果', 'Waiting for data'), 'preflight': ('运行前检查', 'Preflight'), 'locate_region': ('在结构中查看', 'View in structure'), 'locate_molecule': ('在蛋白结构中定位', 'Locate in protein structure'), 'initialize': ('准备运行', 'Prepare run')})

TEXT.update({'input_mode_help': ('请选择下方蛋白状态页并导入结构；多构象请在同一状态中一次选择多个文件。需先验证通过才能运行。', 'Import structures on Protein States; for an ensemble, select multiple files within the same state. Validation must pass before Run.'), 'mode_boundary': ('按所选模式建立空白结构输入栏；科学生成参数保持原值。规则重复模式使用现有 repeat_aggregate 安全门。', 'Create empty structure inputs for this mode; generation settings stay unchanged. Repeat mode uses the existing repeat_aggregate safety gates.')})

TEXT.update({'fast_value': ('从候选区域到分子空间对应与复合物导出', 'From candidate regions to molecular context and complex export'), 'export_complex': ('导出蛋白–配体复合物', 'Export Protein–Ligand Complex'), 'open_sdf': ('打开 SDF', 'Open SDF'), 'complex_value': ('导出当前蛋白与分子的三维组合结构，便于结构观察和后续研究。', 'Export the current protein–molecule structure for visualization and downstream research.'), 'complex_contents': ('导出内容：\n• protein–ligand complex PDB\n• ligand SDF\n• target / molecule info', 'Export contents:\n• protein–ligand complex PDB\n• ligand SDF\n• target / molecule info'), 'select_one': ('请选择一个分子', 'Select one molecule'), 'summary_plot_help': ('查看已有运行汇总图；其中可包含多个目标。', 'View the stored run summary, which may include multiple targets.'), 'journey': ('候选区域 → 区域定位 → 化学挑战 → 分子性质与化学空间 → 三维对应 → 复合物导出', 'Candidate regions → structural location → chemical challenge → properties and chemical space → 3D correspondence → complex export')})
