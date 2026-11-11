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
