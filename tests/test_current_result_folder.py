from pathlib import Path

import pytest
from PySide6.QtWidgets import QApplication

from pathpocket_gui.ux_app import Window


@pytest.fixture
def window(monkeypatch, tmp_path):
    monkeypatch.setenv('PATHPOCKET_USER_HOME', str(tmp_path))
    monkeypatch.setenv('PATHPOCKET_UX_PREFS', str(tmp_path / 'prefs.json'))
    monkeypatch.setenv('PATHPOCKET_LAUNCHER', '/bin/false')
    monkeypatch.setattr(Window, 'discover', lambda self: None)
    app = QApplication.instance() or QApplication([])
    instance = Window()
    yield instance
    instance.close()
    app.processEvents()


@pytest.mark.parametrize('run_name', ['success', 'zero', '失败 task', 'missing'])
def test_current_run_button_targets_exact_recorded_run(window, tmp_path, run_name):
    run = tmp_path / run_name
    if run_name != 'missing':
        run.mkdir()
    opened = []
    window.open_file = opened.append
    window.set_current_run(run)
    assert window.result_run_location.text() == str(run)
    assert window.result_folder_button.isEnabled()
    window.result_folder_button.click()
    assert opened == [run]
    window.set_current_run(None)
    assert not window.result_folder_button.isEnabled()
    assert window.result_run_location.text() == ''


def test_failed_run_path_remains_available(window, tmp_path):
    run = tmp_path / 'failed run'
    run.mkdir()
    window.task = 'run'
    window.on_complete({'status': 'FAIL', 'run_path': str(run), 'error': 'fixture'})
    assert window.loaded_run == run
    assert window.result_run_location.text() == str(run)
    assert window.folder_button.isEnabled()
    assert window.result_folder_button.isEnabled()


def test_result_directory_label_uses_existing_bilingual_vocabulary(window):
    window.mode = 'zh'
    assert window.t('run_folder') == '运行目录'
    window.mode = 'en'
    assert window.t('run_folder') == 'Run folder'

@pytest.mark.parametrize('manifest,summary,targets,expected', [
    ('COMPLETE', 'COMPLETE', [{}], 'Run complete'),
    ('COMPLETE', 'COMPLETE', [], 'Run complete — No targets selected'),
    ('FAILED', 'COMPLETE', [{}], 'Run completion unconfirmed'),
    ('COMPLETE', 'FAILED', [], 'Run completion unconfirmed'),
    (None, 'COMPLETE', [{}], 'Run completion unconfirmed'),
])
def test_result_status_stays_consistent_during_progress_and_language(window, tmp_path, manifest, summary, targets, expected):
    from types import SimpleNamespace
    run = tmp_path / 'run'
    run.mkdir()
    window.index = SimpleNamespace(run=run, manifest={'status': manifest}, summary={'status': summary, 'targets': targets})
    window.set_current_run(run)
    window.mode = 'en'
    window.render_progress()
    assert expected in window.run_status.text()
    assert expected in window.run_context.text()
    if expected == 'Run completion unconfirmed':
        assert str(manifest or 'UNKNOWN') in window.run_status.text()
        window.mode = 'zh'
        window.render_progress()
        assert '运行状态未确认完成' in window.run_status.text()

@pytest.mark.parametrize('language,expected', [('zh', '文件或文件夹不存在'), ('en', 'The file or folder does not exist')])
def test_missing_result_folder_explains_cause(window, tmp_path, monkeypatch, language, expected):
    from pathpocket_gui import ux_app
    warnings = []
    monkeypatch.setattr(ux_app.QMessageBox, 'warning', lambda parent, title, message: warnings.append((title, message)))
    window.mode = language
    missing = tmp_path / 'missing folder'
    window.set_current_run(missing)
    window.result_folder_button.click()
    assert expected in warnings[0][1]
    assert str(missing) in warnings[0][1]


def test_table_uses_target_and_molecule_identity(window):
    from types import SimpleNamespace
    from pathpocket_gui.ux_results import FIELDS
    records = [dict(molecule_id='M001', target_id='target_a'),
               dict(molecule_id='M001', target_id='target_b')]
    window.index = SimpleNamespace(rows=records)
    window.fill(window.mol_table, [[r.get(k) for k in FIELDS] for r in records])
    window.mol_table.selectRow(1)
    assert window.table_row(1) is records[1]
    assert window.selected() == [records[1]]
