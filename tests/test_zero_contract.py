import json
from pathlib import Path
from types import SimpleNamespace
import pandas as pd
from pathpocket.analysis.empty import empty_analysis
from pathpocket.reporting.report import report
from pathpocket.protein.normalization import normalize
from pathpocket.protein.structure import atoms
from test_residue_mapping import write_fixture,SEQ

def test_zero_analysis_has_readable_header_tables(tmp_path,monkeypatch):
    monkeypatch.setattr(pd,'concat',lambda *a,**k:(_ for _ in ()).throw(AssertionError('concat forbidden')))
    result=empty_analysis(tmp_path);assert result['comparisons']==[];assert result['analysis_status']=='NOT_APPLICABLE'
    for path in tmp_path.glob('*.csv'):assert pd.read_csv(path).empty
    assert len(list(tmp_path.glob('*.csv')))==8

def test_zero_report_preserves_old_required_fields(tmp_path):
    out=tmp_path/'08_REPORT';out.mkdir();mapping=dict(status='PASS',mapping_mode='sequence',mapped_chains=2,warnings=[])
    config=SimpleNamespace(name='engineering',states={'a':dict(label='A',structures=['a.pdb'],metadata={})},data=dict(generation=dict(iteration=2),region_discovery=dict(imported_manifest=None)))
    ctx=SimpleNamespace(config=config,root=tmp_path,manifest={'residue_mapping':mapping},path=lambda p:tmp_path/p)
    s=report(ctx,[],[],[],dict(comparisons=[]),[])
    for key in ['project','run_id','status','states','selected_region_families','targets','generation_summary','key_metrics','figures','warnings','limitations']:assert key in s
    assert s['status']=='COMPLETE' and s['target_count']==0;assert s['generation_status']=='SKIPPED';assert s['key_metrics']['generated']==0;assert s['result_class']=='NO_TARGETS'
    assert 'No region family met the current target-selection criteria.' in (out/'report.html').read_text();assert not list(tmp_path.rglob('*.png'))

def test_mapping_gaps_have_no_coordinates(tmp_path):
    a=write_fixture(tmp_path/'a.pdb',[('A',SEQ,0)]);b=write_fixture(tmp_path/'b.pdb',[('X',SEQ[:7]+SEQ[8:],1000)]);before=len(atoms(b))
    normalize([dict(receptor_id='a',state_id='a',path=str(a)),dict(receptor_id='b',state_id='b',path=str(b))],tmp_path)
    df=pd.read_csv(tmp_path/'residue_mapping.csv');gaps=df[df.status=='GAP'];assert len(gaps)==1;assert not gaps.coordinates_present.any();assert len(atoms(b))==before

def test_altloc_does_not_duplicate_residues(tmp_path):
    from pathpocket.protein.residue_mapping import extract_chains
    p=write_fixture(tmp_path/'a.pdb',[('A',SEQ,0)]);lines=p.read_text().splitlines();alternate=lines[0][:16]+'B'+lines[0][17:];p.write_text('\n'.join([lines[0],alternate]+lines[1:]))
    assert len(extract_chains(atoms(p))['A'])==len(SEQ)
