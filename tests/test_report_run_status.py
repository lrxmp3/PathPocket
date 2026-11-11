from types import SimpleNamespace

import pytest

from pathpocket_gui import ux_reports


@pytest.mark.parametrize('manifest,summary,targets,zh,en', [
    ('FAILED', 'COMPLETE', [{}], '运行状态未确认完成', 'Run completion unconfirmed'),
    ('COMPLETE', 'FAILED', [], '运行状态未确认完成', 'Run completion unconfirmed'),
    (None, 'COMPLETE', [{}], '运行状态未确认完成', 'Run completion unconfirmed'),
    ('COMPLETE', 'COMPLETE', [{}], '运行完成', 'Run complete'),
    ('COMPLETE', 'COMPLETE', [], '运行完成 — 未选择目标', 'Run complete — No targets selected'),
])
def test_report_status_matches_both_records(tmp_path, monkeypatch, manifest, summary, targets, zh, en):
    run = tmp_path / 'run'
    run.mkdir()
    index = SimpleNamespace(run=run, manifest={'status': manifest},
                            summary={'status': summary, 'targets': targets},
                            rows=[], figures=[], targets=targets, source_hashes={})
    monkeypatch.setattr(ux_reports, 'write_molecules', lambda *args: {})
    out = tmp_path / 'presentation'
    out.mkdir()
    ux_reports.reports(index, out)
    assert zh in (out / 'report_zh.html').read_text(encoding='utf-8')
    assert en in (out / 'report_en.html').read_text(encoding='utf-8')
    if manifest != 'COMPLETE' or summary != 'COMPLETE':
        assert str(manifest or 'UNKNOWN') in (out / 'report_en.html').read_text(encoding='utf-8')


def test_completed_target_with_zero_molecules_is_explicit(tmp_path, monkeypatch):
    run = tmp_path / 'run'
    run.mkdir()
    summary = {'status': 'COMPLETE', 'targets': [{}], 'key_metrics': {'generated': 0}}
    index = SimpleNamespace(run=run, manifest={'status': 'COMPLETE'}, summary=summary,
                            rows=[], figures=[], targets=[{}], source_hashes={})
    monkeypatch.setattr(ux_reports, 'write_molecules', lambda *args: {})
    out = tmp_path / 'presentation'
    out.mkdir()
    ux_reports.reports(index, out)
    assert '运行完成 — 未生成分子' in (out / 'report_zh.html').read_text(encoding='utf-8')
    assert 'Run complete — No molecules generated' in (out / 'report_en.html').read_text(encoding='utf-8')
