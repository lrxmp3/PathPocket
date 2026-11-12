from types import SimpleNamespace

import pytest
from PySide6.QtCore import QProcess
from pathpocket_gui.ux_app import Window
from pathpocket_gui.ux_i18n import tr


@pytest.mark.parametrize('mode', ['zh', 'en'])
@pytest.mark.parametrize('task,draw,key', [
    (True, QProcess.NotRunning, 'close_busy_task'),
    (False, QProcess.Running, 'close_busy_render'),
])
def test_close_waits_for_active_work(monkeypatch, mode, task, draw, key):
    messages = []
    monkeypatch.setattr('pathpocket_gui.ux_app.QMessageBox.information', lambda parent, title, message: messages.append((title, message)))
    window = SimpleNamespace(bridge=SimpleNamespace(busy=task), draw_process=SimpleNamespace(state=lambda: draw), t=lambda k: tr(k, mode))
    event = SimpleNamespace(ignore=lambda: messages.append('ignored'), accept=lambda: messages.append('accepted'))
    Window.closeEvent(window, event)
    assert messages == [(tr('close_busy_title', mode), tr(key, mode)), 'ignored']


def test_close_allows_idle_window():
    messages = []
    window = SimpleNamespace(bridge=SimpleNamespace(busy=False), draw_process=None)
    event = SimpleNamespace(ignore=lambda: messages.append('ignored'), accept=lambda: messages.append('accepted'))
    Window.closeEvent(window, event)
    assert messages == ['accepted']
