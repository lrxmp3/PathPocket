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


def test_project_path_actions_are_separate_from_path_field(window):
    page = window.pages.widget(0)
    layout = page.layout()
    path_row = layout.itemAt(1).layout()
    action_row = layout.itemAt(2).layout()
    assert path_row.indexOf(window.project_location) >= 0
    copy_button = next(widget for widget, key, method in window.bound if key == 'copy_path')
    assert action_row.indexOf(copy_button) >= 0
    for language, expected in [('zh', '复制路径'), ('en', 'Copy path')]:
        window.lang_combo.setCurrentIndex(window.lang_combo.findData(language))
        assert copy_button.text() == expected


def test_run_path_buttons_are_separate_from_task_buttons(window):
    layout = window.pages.widget(3).layout()
    copies = [widget for widget, key, method in window.bound if key == 'copy_path']
    assert any(layout.itemAt(i).layout() and
               layout.itemAt(i).layout().indexOf(window.folder_button) >= 0 and
               layout.itemAt(i).layout().indexOf(copies[1]) >= 0 and
               layout.itemAt(i).layout().indexOf(window.run_button) < 0
               for i in range(layout.count()))


def test_chinese_controls_inherit_window_font(window):
    from PySide6.QtGui import QFontInfo
    expected = QFontInfo(window.font()).family()
    controls = [widget for widget, key, method in window.bound
                if key in ('workspace', 'copy_path', 'advanced')]
    assert controls
    assert all(QFontInfo(widget.font()).family() == expected for widget in controls)


def test_result_folder_buttons_have_distinct_bilingual_names(window):
    report = next(widget for widget, key, method in window.bound if key == 'open_report_folder')
    for lang, run_text, report_text in [
        ('zh', '打开运行目录', '打开报告目录'),
        ('en', 'Open run folder', 'Open report folder'),
    ]:
        window.lang_combo.setCurrentIndex(window.lang_combo.findData(lang))
        assert window.result_folder_button.text() == run_text
        assert report.text() == report_text


def test_scope_banner_remains_translated_when_language_changes(window):
    window.lang_combo.setCurrentIndex(window.lang_combo.findData('zh'))
    assert window.scope.text() == window.t('fast_value')
    assert '复合物' in window.scope.text()
    assert window.scope.wordWrap()
    window.lang_combo.setCurrentIndex(window.lang_combo.findData('en'))
    assert window.scope.text() == window.t('fast_value')
    assert 'complex' in window.scope.text().lower()
    assert window.scope.wordWrap()


def test_linux_source_uses_installed_simplified_chinese_font(window, monkeypatch, tmp_path):
    import os
    from PySide6.QtGui import QFont, QFontDatabase

    if os.name == 'nt' or 'Noto Sans CJK SC' not in QFontDatabase.families():
        pytest.skip('system simplified Chinese font unavailable')
    app = QApplication.instance()
    original = app.font()
    monkeypatch.setenv('PATHPOCKET_FRONTEND_BUNDLE', str(tmp_path))
    try:
        app.setFont(QFont('DejaVu Sans', 10))
        second = Window()
        assert app.font().family() == 'Noto Sans CJK SC'
        second.close()
    finally:
        app.setFont(original)

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


def test_duplicate_molecule_ids_receive_distinct_export_names():
    from types import SimpleNamespace
    from pathpocket_gui.ux_export import filenames, friendly
    from pathpocket_gui.ux_results import thumb_id
    records = [dict(molecule_id='M000001', target_id='target_a', region_family_id='family'),
               dict(molecule_id='M000001', target_id='target_b', region_family_id='family')]
    index = SimpleNamespace(rows=records)
    names = filenames(index)
    assert len(names) == 2
    assert friendly(index, records[0]).casefold() != friendly(index, records[1]).casefold()
    assert thumb_id(records[0]) != thumb_id(records[1])


def test_interrupted_task_is_not_reported_as_validation_failure(window, tmp_path):
    window.task = 'run'
    window.project_validated = True
    run = tmp_path / 'interrupted run'
    run.mkdir()
    window.mode = 'en'
    window.on_complete({'status': 'INTERRUPTED', 'run_path': str(run), 'error': 'raw diagnostic'})
    assert window.run_status.text() == 'Stopped'
    assert window.loaded_run == run
    assert 'raw diagnostic' in window.log.toPlainText()
    assert window.run_button.isEnabled()
    window.set_current_run(None)
    assert not window.last_run_interrupted


def test_history_uses_interruption_session_without_changing_manifest(window, tmp_path):
    import json
    project = tmp_path / 'project'
    run = project / 'runs' / 'RUN_001'
    run.mkdir(parents=True)
    manifest = run / 'run_manifest.json'
    original = b'{"status":"RUNNING"}'
    manifest.write_bytes(original)
    session = tmp_path / 'sessions' / 'GUI_001'
    session.mkdir(parents=True)
    (session / 'response.json').write_text(json.dumps({'status': 'INTERRUPTED', 'run_path': str(run)}))
    window.project = project
    window.settings['work'] = str(session.parent)
    window.mode = 'en'
    window.refresh_history()
    assert window.history.item(0, 1).text() == 'Stopped (manifest: RUNNING)'
    window.mode = 'zh'
    window.refresh_history()
    assert window.history.item(0, 1).text() == '已停止（清单：RUNNING）'
    assert manifest.read_bytes() == original


def test_iteration_notice_is_available_in_both_languages(window):
    window.mode = 'zh'
    assert '至少需要两轮' in window.t('iteration_notice')
    window.mode = 'en'
    assert 'at least two iterations' in window.t('iteration_notice')
    assert window.iteration.minimum() == 1
