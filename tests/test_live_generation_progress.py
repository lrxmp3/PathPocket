import json

from pathpocket_gui.ux_progress import snapshot


def test_active_targets_have_separate_batch_progress_and_no_invented_molecules(tmp_path):
    (tmp_path / '05_TARGET_SELECTION').mkdir()
    (tmp_path / '05_TARGET_SELECTION/targets.json').write_text(json.dumps([{'target_id': 'T1'}, {'target_id': 'T2'}]))
    target = tmp_path / '06_CHEMICAL_CHALLENGE/T1'
    target.mkdir(parents=True)
    (target / 'generation.log').write_text('Growing Fragments--Step 2: 47%|####| 47/100\r')
    (tmp_path / '06_CHEMICAL_CHALLENGE/T2').mkdir()
    data = snapshot(tmp_path)
    assert data['generated'] is None
    assert data['engine_progress']['T1'] == {'phase': 'growth', 'step': 2, 'percent': 47, 'current': 47, 'total': 100}
    assert data['engine_progress']['T2'] is None


def test_finished_targets_do_not_show_stale_batch_progress(tmp_path):
    (tmp_path / '05_TARGET_SELECTION').mkdir()
    (tmp_path / '05_TARGET_SELECTION/targets.json').write_text('[{"target_id":"T1"}]')
    target = tmp_path / '06_CHEMICAL_CHALLENGE/T1'
    target.mkdir(parents=True)
    (target / 'generation.log').write_text('Placing Initial Fragments: 50%|###| 5/10\n')
    for code in (0, 7):
        (target / 'execution.json').write_text(json.dumps({'returncode': code}))
        assert snapshot(tmp_path)['engine_progress'] == {}


def test_progress_labels_are_bilingual():
    from pathpocket_gui.ux_i18n import TEXT
    for key in ('engine_batch_progress', 'engine_growth', 'engine_placement'):
        assert len(TEXT[key]) == 2 and all(TEXT[key])
