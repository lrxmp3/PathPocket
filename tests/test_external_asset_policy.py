import hashlib
import importlib.util
import json
import os
from pathlib import Path
import subprocess

import pytest


ROOT = Path(__file__).resolve().parents[1]


def installer():
    spec = importlib.util.spec_from_file_location('install_runtime', ROOT / 'distribution/linux/install_runtime.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_missing_and_mismatched_local_assets_are_rejected(monkeypatch, tmp_path):
    module = installer()
    monkeypatch.delenv('PATHPOCKET_ED2MOL_WEIGHTS_ARCHIVE', raising=False)
    with pytest.raises(RuntimeError, match='user-supplied local file'):
        module.supplied_asset('PATHPOCKET_ED2MOL_WEIGHTS_ARCHIVE', '0' * 64)
    path = tmp_path / 'local weights.zip'
    path.write_bytes(b'fixture')
    monkeypatch.setenv('PATHPOCKET_ED2MOL_WEIGHTS_ARCHIVE', str(path))
    with pytest.raises(RuntimeError, match='SHA256'):
        module.supplied_asset('PATHPOCKET_ED2MOL_WEIGHTS_ARCHIVE', '0' * 64)
    assert module.supplied_asset('PATHPOCKET_ED2MOL_WEIGHTS_ARCHIVE', hashlib.sha256(b'fixture').hexdigest()) == path


def test_setup_stops_before_installing_if_assets_are_absent(tmp_path):
    script = ROOT / 'distribution/linux/Setup_First_Run.sh'
    env = dict(os.environ)
    env.pop('PATHPOCKET_ED2MOL_WEIGHTS_ARCHIVE', None)
    env.pop('PATHPOCKET_SMINA_BINARY', None)
    result = subprocess.run(['bash', str(script)], cwd=tmp_path, env=env, capture_output=True, text=True)
    assert result.returncode == 2
    assert 'not downloaded automatically' in result.stdout
    assert not list(tmp_path.iterdir())


def test_installer_does_not_download_when_external_assets_are_missing(monkeypatch, tmp_path):
    module = installer()
    (tmp_path / 'download-lock.json').write_text(json.dumps({'smina': {'sha256': '0' * 64}, 'linux': []}))
    (tmp_path / 'weights-lock.json').write_text(json.dumps({'archive_sha256': '0' * 64}))
    monkeypatch.setattr(module, 'B', tmp_path)
    monkeypatch.delenv('PATHPOCKET_ED2MOL_WEIGHTS_ARCHIVE', raising=False)
    monkeypatch.delenv('PATHPOCKET_SMINA_BINARY', raising=False)
    monkeypatch.setattr(module, 'acquire', lambda *args: pytest.fail('unexpected network/download'))
    with pytest.raises(RuntimeError, match='user-supplied local file'):
        module.main()


def test_installer_does_not_download_when_only_smina_is_missing(monkeypatch, tmp_path):
    module = installer()
    weights = tmp_path / 'user-supplied.zip'
    weights.write_bytes(b'local fixture')
    (tmp_path / 'download-lock.json').write_text(json.dumps({'smina': {'sha256': '0' * 64}, 'linux': []}))
    (tmp_path / 'weights-lock.json').write_text(json.dumps({'archive_sha256': hashlib.sha256(weights.read_bytes()).hexdigest()}))
    monkeypatch.setattr(module, 'B', tmp_path)
    monkeypatch.setenv('PATHPOCKET_ED2MOL_WEIGHTS_ARCHIVE', str(weights))
    monkeypatch.delenv('PATHPOCKET_SMINA_BINARY', raising=False)
    monkeypatch.setattr(module, 'acquire', lambda *args: pytest.fail('unexpected network/download'))
    with pytest.raises(RuntimeError, match='PATHPOCKET_SMINA_BINARY'):
        module.main()
