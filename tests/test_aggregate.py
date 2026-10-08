import json
import numpy as np
import pytest
from pathpocket.protein.aggregate import detect,RepeatResidueID
from pathpocket.protein.repeat_geometry import rigid_rmsd
from pathpocket.protein.local_unit import adapt
from pathpocket.protein.structure import atoms
from repeat_fixtures import stack,SEQ

def coords(path):return np.array([a['xyz'] for a in atoms(path)])
def test_perfect_and_centers(tmp_path):
    d=detect(stack(tmp_path/'a.pdb'));assert d.status=='REPEAT_AGGREGATE_PASS';assert len(d.selected_chains)==5;assert d.central_chain=='D';assert d.geometry.explained_variance>.999;assert abs(d.geometry.spacing_median-4.8)<1e-8;assert d.geometry.spacing_cv<1e-8;assert d.details['max_chain_rmsd_A']<1e-8;assert all(d.details['adjacent_CA_contacts']);assert [c.usable_as_center for c in d.copies]==[False,False,True,True,True,False,False]

def test_rename_reorder_export_identical(tmp_path):
    a=adapt(stack(tmp_path/'a.pdb'),tmp_path/'one');b=adapt(stack(tmp_path/'b.pdb',rename=True,reorder=True),tmp_path/'two');assert open(a.rawframe).read()==open(b.rawframe).read();assert open(a.aligned).read()==open(b.aligned).read();assert [r['canonical_repeat_id'] for r in a.manifest['residue_mapping']]==[r['canonical_repeat_id'] for r in b.manifest['residue_mapping']]

def test_rigid_transform_and_axis_sign(tmp_path):
    # Exact orthogonal transform avoids unrelated PDB decimal quantization.
    rot=np.array([[0,0,1],[1,0,0],[0,1,0.]])
    a=adapt(stack(tmp_path/'a.pdb'),tmp_path/'one');b=adapt(stack(tmp_path/'b.pdb',rotation=rot,translation=[21,-7,13]),tmp_path/'two',reference=a.rawframe)
    assert np.max(abs(coords(a.aligned)-coords(b.aligned)))<.0011;assert b.manifest['orientation']['forward_rmsd_A']<1e-8

@pytest.mark.parametrize('n',[6,8])
def test_terminal_isolation(tmp_path,n):
    a=adapt(stack(tmp_path/'a.pdb'),tmp_path/'one');b=adapt(stack(tmp_path/'b.pdb',n=n),tmp_path/'two');assert rigid_rmsd(coords(a.rawframe),coords(b.rawframe))<1e-8;assert 'CENTRAL_CHOICE_EQUIVALENT' in ' '.join(b.manifest['warnings'])

@pytest.mark.parametrize('kwargs,status',[({'n':5,'ring':True},'AMBIGUOUS_HOMOMER'),({'spacing':[4.8,4.8,15,4.8,1,4.8]},'IRREGULAR_REPEAT_SPACING'),({'lanes':True},'MULTI_PROTOFILAMENT_UNSUPPORTED'),({'n':3},'INSUFFICIENT_REPEAT_COPIES'),({'spacing':[30]*6},'NO_REPEAT_CONTACT')])
def test_negative_controls(tmp_path,kwargs,status):assert detect(stack(tmp_path/'a.pdb',**kwargs)).status==status

def test_inter_repeat_identity(tmp_path):
    u=adapt(stack(tmp_path/'a.pdb'),tmp_path/'out');ids=[r['canonical_repeat_id'] for r in u.manifest['residue_mapping']];assert 'RC_001:0:1' in ids and 'RC_001:+1:1' in ids;assert len(set(ids))==5*len(SEQ)
    for x in ids:assert RepeatResidueID.parse(x).serialize()==x

def test_rawframe_preserves_selected_coordinates(tmp_path):
    p=stack(tmp_path/'a.pdb');u=adapt(p,tmp_path/'out');raw=atoms(p);selected={x['original_chain_id'] for x in u.manifest['prepared_chains']};before=sorted(tuple(x['xyz']) for x in raw if x['residue'].split(':')[0] in selected);after=sorted(tuple(x['xyz']) for x in atoms(u.rawframe));assert before==after

def test_ordinary_mapping_gate_unchanged():
    from pathpocket.protein.chain_mapping import assign_chains
    from pathpocket.protein.residue_mapping import MappingError
    from test_residue_mapping import residues
    with pytest.raises(MappingError,match='AMBIGUOUS'):assign_chains({'A':residues(),'B':residues(chain='B')},{'X':residues(chain='X'),'Y':residues(chain='Y')})

def test_structural_irregularity(tmp_path):
    p=stack(tmp_path/'a.pdb');lines=p.read_text().splitlines()
    for i,l in enumerate(lines):
        if l.startswith('ATOM') and l[21]=='D':lines[i]=l[:30]+f'{float(l[30:38])*2-13.6:8.3f}'+l[38:]
    p.write_text('\n'.join(lines));assert detect(p).status =='STRUCTURALLY_IRREGULAR_REPEAT'

def test_heterogeneous_reject(tmp_path):
    p=stack(tmp_path/'a.pdb');lines=p.read_text().splitlines();lines=[l[:17]+'TRP'+l[20:] if l.startswith('ATOM') and l[21]=='D' else l for l in lines];p.write_text('\n'.join(lines));assert detect(p).status=='HETERO_AGGREGATE_UNSUPPORTED'

def test_failed_export_audit(tmp_path):
    from pathpocket.protein.aggregate import AggregateError
    with pytest.raises(AggregateError):adapt(stack(tmp_path/'ring.pdb',n=5,ring=True),tmp_path/'out')
    q=json.loads((tmp_path/'out/aggregate_qc.json').read_text());assert not q['passed'];assert q['status']=='AMBIGUOUS_HOMOMER';assert not (tmp_path/'out/local_unit_rawframe.pdb').exists()

def test_router_canonical_repeat_identity(tmp_path):
    from pathpocket.protein.structure_mode import prepare_and_normalize
    p=stack(tmp_path/'a.pdb');q=stack(tmp_path/'b.pdb',rename=True,reorder=True);out=tmp_path/'out';out.mkdir()
    recs=[dict(receptor_id='one',state_id='a',path=str(p)),dict(receptor_id='two',state_id='b',path=str(q))];maps,m,s=prepare_and_normalize(recs,out)
    assert s['structure_mode']=='repeat_aggregate';assert m['mapping_mode']=='repeat_equivalence';assert maps['one']==maps['two'];assert maps['one']['C:1:_']=='RC_001:0:1';assert maps['one']['D:1:_']=='RC_001:+1:1'

def test_unequal_central_candidates_stop(tmp_path):
    p=stack(tmp_path/'a.pdb',n=6);lines=p.read_text().splitlines()
    for i,l in enumerate(lines):
        if l.startswith('ATOM') and l[21]=='A':lines[i]=l[:38]+f'{float(l[38:46])+(.8 if int(l[22:26])%2 else -.8):8.3f}'+l[46:]
    p.write_text('\n'.join(lines));assert detect(p).status=='CENTRAL_WINDOW_AMBIGUOUS'

def test_reference_reverse_orientation(tmp_path):
    a=adapt(stack(tmp_path/'a.pdb'),tmp_path/'one');lines=open(a.rawframe).read().splitlines();swap=dict(zip('ABCDE','EDCBA'));p=tmp_path/'reverse.pdb';p.write_text('\n'.join(l[:21]+swap[l[21]]+l[22:] if l.startswith('ATOM') else l for l in lines))
    b=adapt(stack(tmp_path/'b.pdb',rename=True),tmp_path/'two',reference=p);assert b.manifest['orientation']['reversed'];assert b.manifest['orientation']['reverse_rmsd_A']<1e-8

def test_cif_parser_equivalence(tmp_path):
    from Bio.PDB import PDBParser,MMCIFIO
    p=stack(tmp_path/'a.pdb');io=MMCIFIO();io.set_structure(PDBParser(QUIET=True).get_structure('s',p));cif=tmp_path/'a.cif';io.save(str(cif));a=adapt(p,tmp_path/'one');b=adapt(cif,tmp_path/'two');assert np.array_equal(coords(a.rawframe),coords(b.rawframe))

def test_left_terminal_removed(tmp_path):
    p=stack(tmp_path/'a.pdb');a=adapt(p,tmp_path/'one')
    q=tmp_path/'removed.pdb';q.write_text('\n'.join(l for l in p.read_text().splitlines() if not (l.startswith('ATOM') and l[21]=='A')))
    b=adapt(q,tmp_path/'two');assert rigid_rmsd(coords(a.rawframe),coords(b.rawframe))<1e-8

def test_unsupported_window_policy():
    from pathpocket.protein.repeat_geometry import RepeatPolicy
    with pytest.raises(ValueError):RepeatPolicy(repeat_radius=3)
    with pytest.raises(ValueError):RepeatPolicy(min_repeat_copies=3)
