"""View-only guidance; never changes the backend configuration or thresholds."""
MODES={
'single':('单结构候选区域筛查','Single-structure candidate screening','发现单个结构中的候选微区并执行化学挑战；不能得出 state-specific pocket 结论。','Discover candidate microregions and chemically challenge one structure; no state-specific pocket conclusion.'),
'multistate':('多状态蛋白比较','Multi-state protein comparison','为同一蛋白不同状态的候选微区建立 correspondence，比较出现、消失与重塑，再执行统一 ED2Mol chemical challenge；状态定义须有独立依据。','Establish correspondence across states of the same protein, compare region emergence, disappearance and remodeling, then apply a consistent ED2Mol chemical challenge; state labels need independent evidence.'),
'ensemble':('多构象 / MD ensemble','Multi-conformer / MD ensemble','比较已有构象集合中的候选微区；本界面不运行 MD，生成分子不作为生物学重复。','Compare candidate microregions across existing conformer ensembles; this interface does not run MD and generated molecules are not biological replicates.'),
'repeat':('规则 repeat / amyloid','Regular repeat / amyloid','对通过现有规则重复结构安全门的堆叠进行 copy-aware microregion 分析；不绕过 homomer ambiguity 检查。','Copy-aware microregion analysis for stacks passing the existing regular-repeat safety gates; homomer ambiguity checks remain mandatory.')}
DEMO_MODES={'DEMO_CONVENTIONAL_HSA':'single','DEMO_REPEAT_AGGREGATE_7KWZ':'repeat','DEMO_NO_TARGETS':'single'}
DEMO_PURPOSE={
'DEMO_CONVENTIONAL_HSA':('HSA：单结构导入基准区域，验证常规蛋白、化学挑战与结果展示；不是多状态病理比较。','HSA: a single-structure imported-region benchmark for conventional protein, chemical challenge and results display; not a pathological state comparison.'),
'DEMO_REPEAT_AGGREGATE_7KWZ':('7KWZ：规则 repeat / amyloid 导入基准区域，验证五-copy映射、跨-repeat区域和生成链路；不是 monomer–amyloid 比较。','7KWZ: a regular repeat / amyloid imported-region benchmark for five-copy mapping, inter-repeat regions and generation; not a monomer–amyloid comparison.'),
'DEMO_NO_TARGETS':('空目标工程用例：验证无候选区域时安全完成；不是科学阴性对照。','Zero-target engineering case: validates safe completion without candidates; not a scientific negative control.')}
def describe(key,zh=True):
 a=MODES.get(key,MODES['single']);return a[0 if zh else 1]+'\n'+a[2 if zh else 3]
def infer(config,run=None):
 from pathlib import Path
 if run and (Path(run)/'01_VALIDATE/aggregate').is_dir():return 'repeat'
 states=config.get('protein',{}).get('states',{})
 if len(states)>1:return 'multistate'
 if any(len(s.get('structures',[]))>1 for s in states.values()):return 'ensemble'
 return 'single'

def input_scaffold(config,mode):
 """New-project input form only; preserve all generation/runtime/science settings."""
 import copy
 result=copy.deepcopy(config)
 states={'state_A':{'label':'Structure A','order':0,'structures':[]}}
 if mode=='multistate':states['state_B']={'label':'Structure B','order':1,'structures':[]}
 if mode=='ensemble':states['state_A']['label']='Conformer ensemble'
 if mode=='repeat':states['state_A']['label']='Regular repeat stack'
 result['protein']['states']=states
 if mode=='repeat':result['protein']['structure_mode']='repeat_aggregate'
 return result

# Ordinary UI foregrounds purpose; detailed boundaries remain in Advanced Help/docs.
MODE_VALUE={
'single':('发现单个结构中的候选微区，并查看对应化学挑战结果。','Discover candidate microregions in one structure and explore their chemical-challenge results.'),
'multistate':('建立同一蛋白跨状态微区的对应关系，比较区域出现、消失与重塑，再执行统一化学挑战。','Match microregions across protein states, compare emergence, disappearance and remodeling, then apply consistent chemical challenges.'),
'ensemble':('比较已有构象集合中的候选微区与化学性质空间。','Compare candidate microregions and chemical-property space across existing conformer ensembles.'),
'repeat':('在规则重复堆叠中查看具有 repeat 身份的微区与生成分子。','Explore copy-aware microregions and generated molecules in regular repeat stacks.')}
def describe(key,zh=True):
 a=MODES.get(key,MODES['single']);return a[0 if zh else 1]+'\n'+MODE_VALUE.get(key,MODE_VALUE['single'])[0 if zh else 1]
