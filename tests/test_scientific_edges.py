import json
from pathlib import Path
import numpy as np
import pytest
from rdkit import Chem
from rdkit.Chem import AllChem
from pathpocket.protein.structure import atoms
from pathpocket.regions.homology import targets_for_family
from pathpocket.analysis.generation_qc import analyze_target
from pathpocket.core.run_context import RunContext,write_json

def pdb(path,offset=0):
    lines=[]
    for i,(x,y,z) in enumerate([(0,0,0),(2,0,0),(0,3,0),(0,0,4)],1):
        lines.append(f'ATOM  {i:5d}  CA  ALA A{i:4d}    {x+offset:8.3f}{y:8.3f}{z:8.3f}  1.00 20.00           C  ')
    path.write_text('\n'.join(lines)+'\nEND\n')

def test_homologous_fallback_is_not_detection(tmp_path):
    a=tmp_path/'a.pdb';b=tmp_path/'b.pdb';pdb(a);pdb(b,10);out=tmp_path/'targets';out.mkdir()
    family=dict(region_family_id='RF_1',members=['i1'],center=[0,0,0],consensus_residues=[f'A:{i}:_' for i in range(1,5)],state_occurrence={'a':1.,'b':0.},role='emergent')
    instances=[dict(region_instance_id='i1',receptor_id='r1',state_id='a',center=[0,0,0])];receptors=[dict(receptor_id='r1',state_id='a',aligned=str(a)),dict(receptor_id='r2',state_id='b',aligned=str(b))]
    result=targets_for_family(family,instances,receptors,out)
    assert result[0]['detected_pocket'] and not result[1]['detected_pocket'];assert result[1]['local_fit_RMSD_A']<1e-10
    xyz=np.array([a['xyz'] for a in atoms(result[1]['full_receptor'])]);assert np.allclose(xyz[0],[0,0,0])

def test_generation_qc_duplicates_and_bad_geometry(tmp_path):
    (tmp_path/'raw').mkdir();pdb(tmp_path/'receptor_full.pdb',100)
    axis=np.arange(-3,3,.5);xyz=np.array(np.meshgrid(axis,axis,axis,indexing='ij')).reshape(3,-1).T;np.save(tmp_path/'raw/ligED.npy',np.column_stack([xyz,np.ones(len(xyz))]))
    m=Chem.AddHs(Chem.MolFromSmiles('CCO'));AllChem.EmbedMolecule(m,randomSeed=42);m.SetProp('qscore','3')
    writer=Chem.SDWriter(str(tmp_path/'raw/output.sdf'));writer.write(m);writer.write(m);bad=Chem.Mol(m);bad.GetConformer().SetAtomPosition(0,(100,100,100));writer.write(bad);writer.close()
    target=dict(target_id='t',region_family_id='f',state_id='x');df,s,ms=analyze_target(tmp_path,target,3)
    assert s['generated']==3 and s['valid']==2 and s['unique']==1;assert len(ms)==1;assert not df.iloc[2].valid
    assert s['physical_compatible']==1;assert df.iloc[0].Q_total_normalized==1

def test_atomic_json_replacement(tmp_path):
    p=tmp_path/'value.json';write_json(p,{'status':'RUNNING'});write_json(p,{'status':'COMPLETE'});assert json.loads(p.read_text())['status']=='COMPLETE';assert not p.with_name('value.json.writing').exists()

def test_registry_detects_symlink_escape(tmp_path):
    from pathpocket.core.paths import guard_write
    allowed=tmp_path/'allowed';allowed.mkdir();outside=tmp_path/'outside';outside.mkdir();(allowed/'escape').symlink_to(outside,target_is_directory=True)
    with pytest.raises(ValueError):guard_write(allowed/'escape/file',allowed)

def test_empty_generation_is_reportable(tmp_path):
    from pathpocket.analysis.chemical_space import profile
    (tmp_path/'raw').mkdir();(tmp_path/'raw/output.sdf').write_text('');pdb(tmp_path/'receptor_full.pdb',100)
    np.save(tmp_path/'raw/ligED.npy',np.array([[0.,0.,0.,1.],[.5,0,0,1.]]))
    df,summary,mols=analyze_target(tmp_path,dict(target_id='t',region_family_id='f',state_id='s'),100)
    assert summary['generated']==summary['unique']==0 and summary['median_Q_normalized'] is None
    result=profile(df,mols,tmp_path);assert result['comparisons']==[]
    assert np.load(tmp_path/'fingerprints.npz')['bits'].shape==(0,2048)
