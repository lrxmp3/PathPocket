from types import SimpleNamespace

from pathpocket_gui.ux_app import Window


def test_completed_molecule_results_start_read_only_2d_render():
    calls=[]
    window=SimpleNamespace(index=SimpleNamespace(rows=[{'molecule_id':'M1'}]),presentation=None)
    window.prepare_presentation=lambda: calls.append('render')
    Window.prepare_result_presentation(window)
    assert calls==['render']


def test_zero_target_results_do_not_start_2d_render():
    calls=[]
    window=SimpleNamespace(index=SimpleNamespace(rows=[]),presentation=None)
    window.prepare_presentation=lambda: calls.append('render')
    Window.prepare_result_presentation(window)
    assert calls==[]


def test_existing_presentation_is_not_rebuilt_automatically():
    calls=[]
    window=SimpleNamespace(index=SimpleNamespace(rows=[{'molecule_id':'M1'}]),presentation='existing')
    window.prepare_presentation=lambda: calls.append('render')
    Window.prepare_result_presentation(window)
    assert calls==[]
