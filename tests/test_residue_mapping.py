import json
import numpy as np
import pytest
from pathpocket.protein.residue_mapping import *
from pathpocket.protein.chain_mapping import assign_chains
from pathpocket.protein.normalization import normalize
from pathpocket.protein.structure import atoms

SEQ='ACDEFGHIKLMNPQRSTVWY'
def residues(seq=SEQ,chain='A',offset=0):
    inverse={v:k for k,v in AA.items()}
    return [dict(raw_id=f'{chain}:{i+1+offset}:_',aa=a,resname=inverse[a]) for i,a in enumerate(seq)]
def write_fixture(path,chains):
    lines=[]
    for chain,seq,offset in chains:
        for i,r in enumerate(residues(seq,chain,offset)):
            n=offset+i+1;lines.append(f'ATOM  {len(lines)+1:5d}  CA  {r["resname"]:3s} {chain}{n:4d}    {i*2.:8.3f}{float(i*i%7):8.3f}{float(i*i*i%11):8.3f}  1.00 20.00           C  ')
    path.write_text('\n'.join(lines)+'\nEND\n');return path
def test_raw_and_canonical_roundtrip():
    r=RawResidueID('X',1001,'B');assert RawResidueID.parse(r.serialize())==r
    c=CanonicalResidueID('REF_001',2,'CYS');assert CanonicalResidueID.parse(c.serialize())==c
def test_extraction_and_insertion(tmp_path):
    p=write_fixture(tmp_path/'a.pdb',[('A',SEQ,0)]);lines=p.read_text().splitlines();lines[1]=lines[1][:22]+'   1'+'A'+lines[1][27:];p.write_text('\n'.join(lines))
    chain=extract_chains(atoms(p))['A'];assert chain[1]['raw_id']=='A:1:A';assert ''.join(x['aa'] for x in chain)==SEQ
def test_nonstandard_is_not_silent(tmp_path):
    p=write_fixture(tmp_path/'a.pdb',[('A',SEQ,0)]);p.write_text(p.read_text().replace('ALA','MSE'))
    with pytest.raises(MappingError,match='UNSUPPORTED_RESIDUE'):extract_chains(atoms(p))
def test_identity_does_not_align(monkeypatch):
    import pathpocket.protein.chain_mapping as mod
    monkeypatch.setattr(mod,'sequence_mapping',lambda *_:pytest.fail('identity fast path called sequence alignment'))
    result=assign_chains({'A':residues()},{'A':residues()});assert result[0].residue_mapping.mode=='identity'
@pytest.mark.parametrize('chain,offset',[('X',0),('A',1000),('X',1000)])
def test_sequence_renumber(chain,offset):
    m=assign_chains({'A':residues()},{chain:residues(chain=chain,offset=offset)})[0]
    assert m.target_chain==chain and m.residue_mapping.confidence.identity==1
    assert m.residue_mapping.target_to_reference==dict(enumerate(range(len(SEQ))));assert not m.residue_mapping.alignment_ambiguous
def test_missing_internal_gap():
    result=assign_chains({'A':residues()},{'X':residues(SEQ[:7]+SEQ[8:],chain='X',offset=1000)})[0]
    assert result.status=='PASS_WITH_GAPS';assert result.residue_mapping.confidence.gap_count==1
    assert result.residue_mapping.target_to_reference[7]==8
def test_low_confidence():
    with pytest.raises(MappingError,match='LOW_CONFIDENCE'):assign_chains({'A':residues()},{'X':residues('W'*len(SEQ),chain='X')})
def test_distinct_permuted_chains():
    out=assign_chains({'A':residues(),'B':residues(SEQ[::-1],'B')},{'Y':residues(SEQ[::-1],'Y',1000),'X':residues(SEQ,'X',2000)})
    assert {x.reference_chain:x.target_chain for x in out}=={'A':'X','B':'Y'}
def test_homomer_ambiguous():
    with pytest.raises(MappingError,match='AMBIGUOUS'):assign_chains({'A':residues(),'B':residues(chain='B')},{'Y':residues(chain='Y'),'X':residues(chain='X')})
def test_canonical_normalization_keeps_chains_distinct(tmp_path):
    a=write_fixture(tmp_path/'a.pdb',[('A',SEQ,0),('B',SEQ[::-1],0)]);b=write_fixture(tmp_path/'b.pdb',[('Y',SEQ[::-1],1000),('X',SEQ,2000)])
    before=b.read_bytes();recs=[dict(receptor_id='r1',state_id='state_A',path=str(a)),dict(receptor_id='r2',state_id='state_B',path=str(b))]
    maps,summary=normalize(recs,tmp_path);assert b.read_bytes()==before;assert len(set(maps['r1'].values()))==2*len(SEQ)
    assert maps['r1']['A:1:_']==maps['r2']['X:2001:_'];assert maps['r1']['B:1:_']==maps['r2']['Y:1001:_']
    assert summary['mapping_mode']=='sequence';assert (tmp_path/'chain_mapping.csv').exists()
def test_ambiguous_failure_preserves_audit(tmp_path):
    a=write_fixture(tmp_path/'a.pdb',[('A',SEQ,0),('B',SEQ,0)]);b=write_fixture(tmp_path/'b.pdb',[('X',SEQ,1000),('Y',SEQ,2000)])
    with pytest.raises(MappingError,match='AMBIGUOUS'):normalize([dict(receptor_id='r1',state_id='a',path=str(a)),dict(receptor_id='r2',state_id='b',path=str(b))],tmp_path)
    assert json.loads((tmp_path/'mapping_summary.json').read_text())['status']=='AMBIGUOUS'
def test_label_change_preserves_union_with_terminal_residues(tmp_path):
    a=write_fixture(tmp_path/'a.pdb',[('A',SEQ[1:-1],1)]);b=write_fixture(tmp_path/'b.pdb',[('A',SEQ,0)]);x=write_fixture(tmp_path/'x.pdb',[('X',SEQ,1000)])
    def run(second,name):
        out=tmp_path/name;out.mkdir();return normalize([dict(receptor_id='r1',state_id='a',path=str(a)),dict(receptor_id='r2',state_id='b',path=str(second))],out)
    original,one=run(b,'original');renamed,two=run(x,'renamed');assert set(original['r2'].values())==set(renamed['r2'].values());assert original['r1']==renamed['r1']
