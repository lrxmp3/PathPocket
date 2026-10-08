import json,shutil
from pathlib import Path

from pathpocket_gui.portable_projects import copy_demo,verified_no_targets_fixture,ENGINEERING_FIXTURE_FILE

ROOT=Path(__file__).resolve().parents[1]
TEMPLATE=ROOT/'examples/fixtures/DEMO_NO_TARGETS'

def workspace(tmp_path):
    root=tmp_path/'workspace';(root/'20_PROJECTS').mkdir(parents=True);return root

def configure(monkeypatch):
    monkeypatch.setenv('PATHPOCKET_FRONTEND_BUNDLE',str(ROOT))
    monkeypatch.setenv('PATHPOCKET_RUNTIME_ROOT',str(ROOT/'_test_runtime'))

def test_only_canonical_builtin_demo_receives_fixture_marker(tmp_path,monkeypatch):
    configure(monkeypatch);root=workspace(tmp_path)
    project=copy_demo(TEMPLATE,root,'DEMO_NO_TARGETS_TEST')
    marker=verified_no_targets_fixture(project)
    assert marker and marker['fixture_id']=='builtin_no_targets_v1'
    fake=tmp_path/'DEMO_NO_TARGETS';shutil.copytree(TEMPLATE,fake)
    ordinary=copy_demo(fake,root,'SAME_NAME_IS_ORDINARY')
    assert not (ordinary/ENGINEERING_FIXTURE_FILE).exists()

def test_fixture_binding_fails_closed_after_copy_rename_or_config_change(tmp_path,monkeypatch):
    configure(monkeypatch);root=workspace(tmp_path)
    project=copy_demo(TEMPLATE,root,'BOUND_FIXTURE')
    copied=root/'20_PROJECTS'/'COPIED_FIXTURE';shutil.copytree(project,copied)
    assert verified_no_targets_fixture(copied) is None
    config=project/'project.yml';config.write_text(config.read_text()+'\n# changed\n')
    assert verified_no_targets_fixture(project) is None

def test_runner_rejects_tampered_marker(tmp_path,monkeypatch):
    configure(monkeypatch);root=workspace(tmp_path)
    project=copy_demo(TEMPLATE,root,'TAMPERED_FIXTURE');marker=project/ENGINEERING_FIXTURE_FILE
    data=json.loads(marker.read_text());data['fixture_id']='forged';marker.write_text(json.dumps(data))
    from pathpocket_gui.engineering_fixture_runner import verify
    try:verify(project/'project.yml',marker)
    except ValueError as exc:assert 'identity check failed' in str(exc)
    else:raise AssertionError('tampered marker was accepted')

def test_runner_installs_packaged_path_transport(tmp_path):
    calls=tmp_path/'calls.txt'
    (tmp_path/'archive_transport.py').write_text(
        'from pathlib import Path\n'
        f"def install(root): Path({str(calls)!r}).write_text(str(root))\n"
    )
    from pathpocket_gui.engineering_fixture_runner import install_packaged_transport
    assert install_packaged_transport(tmp_path) is True
    assert calls.read_text()==str(tmp_path)
    assert install_packaged_transport(tmp_path/'missing') is False

def test_normal_demos_never_receive_fixture_marker(tmp_path,monkeypatch):
    configure(monkeypatch);root=workspace(tmp_path)
    for name in ['DEMO_CONVENTIONAL_HSA','DEMO_REPEAT_AGGREGATE_7KWZ']:
        project=copy_demo(ROOT/'examples/fixtures'/name,root,name+'_TEST')
        assert verified_no_targets_fixture(project) is None
        assert not (project/ENGINEERING_FIXTURE_FILE).exists()
