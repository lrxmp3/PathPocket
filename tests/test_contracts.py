import json,copy
from pathlib import Path
import numpy as np
import pytest
from rdkit import Chem
from pathpocket.config.schema import validate_data
from pathpocket.config.loader import UniqueLoader
from pathpocket.core.paths import windows_to_wsl,wsl_to_windows,guard_write,safe_id
from pathpocket.core.run_context import RunContext
from pathpocket.core.provenance import sha256
from pathpocket.regions.models import load_targets
from pathpocket.regions.matching import match_regions
from pathpocket.regions.selection import select_families
from pathpocket.protein.structure import fit
from pathpocket.engines.ed2mol import build_config
from pathpocket.analysis.descriptors import describe
from pathpocket.analysis.chemical_space import fingerprint
from pathpocket.reporting.report import make_summary,HEADINGS
import yaml

@pytest.fixture
def config(tmp_path):
    p=tmp_path/'input.pdb';p.write_text('fixture');ini=tmp_path/'template.ini';ini.write_text('[lib]\ncores = a\n[model]\ngppm = w\n[sample]\niteration =\nreference_core = old\n')
    d=dict(project=dict(name='arbitrary',profile='fast',output_root=str(tmp_path/'20_PROJECTS/arbitrary')),protein=dict(states={'WT':dict(structures=[str(p)],order=1),'variant':dict(structures=[str(p)],order=2)}),runtime=dict(ed2mol_root=str(tmp_path),python=str(p),fpocket=str(p),template_config=str(ini)))
    source=tmp_path/'project.yml';source.write_text(yaml.safe_dump(d));return validate_data(d,source,tmp_path)

def test_state_abstraction_defaults(config):
    assert list(config.states)==['WT','variant'];assert config.data['generation']['iteration']==2

@pytest.mark.parametrize('value',[0,-1,True,1.2,'two'])
def test_bad_iteration(config,value):
    d=copy.deepcopy(config.data);d['generation']['iteration']=value
    with pytest.raises(ValueError):validate_data(d,config.source,config.workspace)

@pytest.mark.parametrize('change',[{'molecules':0},{'engine':'other'},{'mode':'hit'},{'seed':-1}])
def test_bad_generation(config,change):
    d=copy.deepcopy(config.data);d['generation'].update(change)
    with pytest.raises(ValueError):validate_data(d,config.source,config.workspace)

def test_duplicate_yaml():
    with pytest.raises(ValueError,match='Duplicate'):yaml.load('states:\n  WT: 1\n  WT: 2',Loader=UniqueLoader)

def test_missing_receptor(config):
    config.data['protein']['states']['WT']['structures']=['missing.pdb']
    with pytest.raises(ValueError,match='does not exist'):validate_data(config.data,config.source,config.workspace)

def test_paths_and_legacy(config):
    assert windows_to_wsl('X:\\data\\a.pdb')=='/mnt/x/data/a.pdb';assert wsl_to_windows('/mnt/x/data/a.pdb')=='X:\\data\\a.pdb'
    for path in [config.workspace.parent/'legacy/file',config.output/'../../../../escape']:
        with pytest.raises(ValueError):guard_write(path,config.output)
    link=config.output;link.parent.mkdir(parents=True);link.symlink_to(config.workspace.parent,target_is_directory=True)
    with pytest.raises(ValueError):guard_write(link/'escape',config.workspace/'20_PROJECTS')

def test_output_escape(config):
    config.data['project']['output_root']=str(config.workspace.parent/'legacy')
    with pytest.raises(ValueError):validate_data(config.data,config.source,config.workspace)

def test_unique_runs_registry_progress(config):
    a=RunContext(config);b=RunContext(config);assert a.root!=b.root
    p=a.path('01_VALIDATE/value.txt');p.write_text('result');aid=a.register(p,'validate','test')
    item=json.loads(a.path('artifacts.json').read_text())[0];assert item['sha256']==sha256(p) and item['artifact_id']==aid
    with pytest.raises(ValueError):a.register(p,'validate','duplicate')
    events=[json.loads(x) for x in a.path('progress.jsonl').read_text().splitlines()];assert events[0]['status']=='running'
    a.finish('FAIL',recovery_point='input');assert json.loads(a.path('run_manifest.json').read_text())['recovery_point']=='input'

def test_fixed_and_auto(config):
    t={'center':[1,2,3]};fixed=build_config(config.data['runtime'],config.data['generation'],t,config.output)
    assert fixed['sample']['iteration']=='2' and fixed['sample']['reference_core']==''
    config.data['generation']['iteration']='auto';assert build_config(config.data['runtime'],config.data['generation'],t,config.output)['sample']['iteration']==''

def test_matching_stability_and_no_invented_control():
    instances=[dict(region_instance_id=str(i),receptor_id=str(i),state_id=s,center=[x,0,0],residues=['A:1:_','A:2:_']) for i,(s,x) in enumerate([('WT',0),('variant',1),('variant',30)])]
    receptors=[dict(receptor_id=x['receptor_id'],state_id=x['state_id']) for x in instances]
    families=match_regions(instances,receptors,sensitivity=False);assert len(families)==2 and families[0]['matching_stability'] is None
    selected=select_families(families,2);assert not any(f['strict_state_stable_control'] for f in selected)
    assert match_regions(instances,receptors,sensitivity=True)[0]['matching_stability']==1

def test_alignment_known_transform():
    x=np.array([[0,0,0],[2,0,0],[0,3,0],[0,0,4]]);y=x+[12,-3,7];r,t,e=fit(x,y);assert e<1e-10;assert np.allclose(x@r+t,y)

def test_descriptors_fingerprint():
    m=Chem.MolFromSmiles('CCO');d=describe(m);assert 46<d['MW']<47;assert d['HBD']==1 and d['formal_charge']==0
    assert fingerprint(m).GetNumBits()==2048;assert d['scaffold']=='ACYCLIC'

def test_import_nonfinite_and_state(config,tmp_path):
    t=dict(target_id='t',region_family_id='r',state_id='WT',center=[float('nan'),0,0],receptor=config.states['WT']['structures'][0],full_receptor=config.states['WT']['structures'][0],detected_pocket=False)
    p=tmp_path/'t.json';p.write_text(json.dumps(dict(targets=[t],families=[dict(region_family_id='r',state_occurrence={'WT':1.0})])))
    with pytest.raises(ValueError,match='finite'):load_targets(p,{'WT'})

def test_report_contract(config):
    ctx=RunContext(config);s=make_summary(ctx,[],[],[],{'comparisons':[]},[])
    assert len(HEADINGS)==12;assert set(['project','run_id','status','states','selected_region_families','targets','generation_summary','key_metrics','figures','warnings','limitations','next_step'])<=s.keys()
    assert any('No strict' in x for x in s['limitations'])

def test_core_no_case_constants():
    root=Path(__file__).parents[1]/'src/pathpocket'
    forbidden=['B'+'SA','PF_'+'090','PF_'+'013','PF_'+'003','37'+'C','52'+'C','82'+'C']
    for p in root.rglob('*.py'):
        assert not any(s in p.read_text() for s in forbidden),p
