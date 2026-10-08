"""Validated generic configuration, with unknown keys rejected."""
from dataclasses import dataclass
from pathlib import Path
import math
from pathpocket.core.paths import native_path, safe_id, guard_write

DEFAULTS = {
 'region_discovery': {'engine':'fpocket', 'top_n':10, 'imported_manifest':None},
 'region_matching': {'centroid_cutoff_A':6.0, 'residue_jaccard_min':0.30, 'sensitivity_analysis':False},
 'target_selection': {'max_region_families':3, 'include_comparator':True},
 'generation': {'engine':'ed2mol', 'mode':'de_novo', 'molecules':100, 'seed':42, 'iteration':2, 'timeout_seconds':7200, 'max_parallel_targets':1, 'retain_cores_num':None, 'retain_mols_num':None},
 'analysis': {'chemical_space':True, 'ed_metrics':True, 'descriptors':True, 'scaffolds':True, 'state_comparison':True},
 'report': {'markdown':True, 'html':True, 'figures_png_dpi':600, 'svg':True},
}

@dataclass
class ProjectConfig:
    data: dict
    source: Path
    workspace: Path
    output: Path
    @property
    def states(self): return self.data['protein']['states']
    @property
    def name(self): return self.data['project']['name']

def require(condition, message):
    if not condition: raise ValueError(message)

def validate_data(raw, source, workspace):
    import copy
    d = copy.deepcopy(raw); source = native_path(source); workspace = native_path(workspace)
    require(isinstance(d,dict), 'Config must be a mapping')
    require(not set(d)-{'project','protein','runtime',*DEFAULTS}, 'Unsupported config section')
    for key in ['project','protein','runtime']: require(isinstance(d.get(key),dict), f'Missing {key} mapping')
    require(not set(d['project'])-{'name','profile','output_root'}, 'Unknown project option')
    safe_id(d['project'].get('name')); require(d['project'].get('profile','fast')=='fast', 'Only profile: fast is supported')
    output = native_path(d['project'].get('output_root',workspace/'20_PROJECTS'/d['project']['name']),source.parent)
    guard_write(output,workspace/'20_PROJECTS'); require(output != workspace/'20_PROJECTS','Output must be a project subdirectory')
    d['project'].update(profile='fast',output_root=str(output))
    require('states' in d['protein'] and not set(d['protein'])-{'states','structure_mode'},'protein supports states and structure_mode')
    d['protein'].setdefault('structure_mode','auto')
    require(d['protein']['structure_mode'] in ['auto','conventional','repeat_aggregate'],'Invalid protein.structure_mode')
    states=d['protein']['states']; require(isinstance(states,dict) and len(states)>=1,'At least one state is required')
    for i,(sid,state) in enumerate(states.items()):
        safe_id(sid); require(isinstance(state,dict),f'Invalid state {sid}')
        require(not set(state)-{'label','order','metadata','structures'},f'Unknown state option: {sid}')
        require(isinstance(state.get('structures'),list) and bool(state['structures']),f'State {sid} has no structures')
        state.setdefault('label',sid); state.setdefault('order',i); state.setdefault('metadata',{})
        require(isinstance(state['order'],int) and not isinstance(state['order'],bool),'state order must be integer')
        require(isinstance(state['metadata'],dict),'state metadata must be mapping')
        state['structures']=[str(native_path(p,source.parent)) for p in state['structures']]
        for p in state['structures']: require(Path(p).is_file(),f'Receptor file does not exist: {p}')
        require(len(set(state['structures']))==len(state['structures']),f'Duplicate receptor in state {sid}')
    require(len({s['order'] for s in states.values()})==len(states),'State orders must be unique')
    d['protein']['states']=dict(sorted(states.items(),key=lambda item:item[1]['order']))
    for section,defaults in DEFAULTS.items():
        supplied=d.get(section,{})
        require(isinstance(supplied,dict) and not set(supplied)-set(defaults),f'Unknown {section} option')
        d[section]={**defaults,**supplied}
    disc=d['region_discovery']; gen=d['generation']; match=d['region_matching']
    require(disc['engine']=='fpocket','Only fpocket discovery supported')
    require(gen['engine']=='ed2mol' and gen['mode']=='de_novo','Only ED2Mol de_novo supported')
    for label,n,lo,hi in [('molecules',gen['molecules'],1,10000),('top_n',disc['top_n'],1,100),('max_region_families',d['target_selection']['max_region_families'],1,20),('timeout_seconds',gen['timeout_seconds'],1,86400),('seed',gen['seed'],0,2**32-1)]:
        require(type(n) is int and lo<=n<=hi,f'{label} must be integer in {lo}..{hi}')
    require(gen['iteration']=='auto' or (type(gen['iteration']) is int and gen['iteration']>=1),'iteration must be a positive integer or auto')
    require(type(gen['max_parallel_targets']) is int and 1<=gen['max_parallel_targets']<=2,'max_parallel_targets must be 1 or 2')
    for key in ['retain_cores_num','retain_mols_num']: require(gen[key] is None or (type(gen[key]) is int and gen[key]>0),f'{key} must be positive integer')
    require(isinstance(match['centroid_cutoff_A'],(int,float)) and math.isfinite(match['centroid_cutoff_A']) and match['centroid_cutoff_A']>0,'Invalid centroid cutoff')
    require(0<=match['residue_jaccard_min']<=1,'residue_jaccard_min must be in [0,1]')
    for section,keys in [('analysis',list(d['analysis'])),('report',['markdown','html','svg']),('region_matching',['sensitivity_analysis']),('target_selection',['include_comparator'])]:
        for key in keys: require(type(d[section][key]) is bool,f'{section}.{key} must be boolean')
    require(all(d['analysis'].values()),'v0.1 requires all analysis modules; partial profiles are not implemented')
    require(d['report']['markdown'] and d['report']['html'] and d['report']['svg'],'v0.1 requires standard Markdown, HTML and SVG outputs')
    require(type(d['report']['figures_png_dpi']) is int and d['report']['figures_png_dpi']>=600,'PNG DPI must be >=600')
    runtime=d['runtime']; require(not set(runtime)-{'ed2mol_root','python','fpocket','template_config'},'Unknown runtime option')
    for key in ['ed2mol_root','python','fpocket','template_config']:
        require(key in runtime,f'Missing runtime.{key}'); runtime[key]=str(native_path(runtime[key],source.parent))
        require(Path(runtime[key]).exists(),f'Runtime path missing: {key}: {runtime[key]}')
    if disc['imported_manifest']:
        disc['imported_manifest']=str(native_path(disc['imported_manifest'],source.parent)); require(Path(disc['imported_manifest']).is_file(),'Imported manifest missing')
        from pathpocket.regions.models import load_targets
        load_targets(Path(disc['imported_manifest']),set(states))
    return ProjectConfig(d,source,workspace,output)
