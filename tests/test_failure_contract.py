import json
from pathlib import Path
from types import SimpleNamespace
import pytest
from pathpocket.workflows.fast_screening import execute

def test_failed_structure_preserved_without_downstream(tmp_path,monkeypatch):
    source=tmp_path/'project.yml';source.write_text('fixture: true')
    bad=tmp_path/'bad.pdb';bad.write_text('NOT A PDB')
    config=SimpleNamespace(workspace=tmp_path,output=tmp_path/'20_PROJECTS/test',source=source,data={},states={'arbitrary':{'structures':[str(bad)]}})
    monkeypatch.setattr('pathpocket.workflows.fast_screening.capture',lambda c:{'test_fixture':True})
    with pytest.raises(RuntimeError,match='preserved run'):execute(config)
    runs=list((config.output/'runs').glob('RUN_*'));assert len(runs)==1
    manifest=json.loads((runs[0]/'run_manifest.json').read_text());assert manifest['status']=='FAIL' and manifest['failed_step']=='01_VALIDATE'
    assert (runs[0]/'00_INPUTS/arbitrary_R0001.pdb').read_text()=='NOT A PDB'
    assert not (runs[0]/'08_REPORT/report.html').exists();assert manifest['recovery_point']
    events=[json.loads(x) for x in (runs[0]/'progress.jsonl').read_text().splitlines()];assert events[-1]['status']=='FAIL'
