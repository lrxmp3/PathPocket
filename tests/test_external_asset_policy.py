import hashlib
import importlib.util
import io
import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]


def installer():
    spec = importlib.util.spec_from_file_location('install_runtime', ROOT / 'distribution/linux/install_runtime.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_external_download_uses_locked_sources_before_install(monkeypatch, tmp_path):
    module = installer()
    weights = {'url': 'https://example.invalid/weights.zip', 'archive_sha256': 'a' * 64}
    smina = {'url': 'https://example.invalid/smina.static', 'sha256': 'b' * 64}
    (tmp_path / 'weights-lock.json').write_text(json.dumps(weights))
    (tmp_path / 'download-lock.json').write_text(json.dumps({'smina': smina, 'linux': []}))
    monkeypatch.setattr(module, 'B', tmp_path)
    calls = []
    def acquire(item, cache):
        calls.append((item, cache))
        if len(calls) == 2:
            raise RuntimeError('stop before installation')
        return tmp_path / 'weights.zip'
    monkeypatch.setattr(module, 'acquire', acquire)
    with pytest.raises(RuntimeError, match='stop before installation'):
        module.main()
    assert calls == [({'url': weights['url'], 'sha256': weights['archive_sha256'], 'filename': 'weights.zip'}, tmp_path / 'runtime/downloads'), (smina, tmp_path / 'runtime/downloads')]


def test_acquire_checks_sha256(monkeypatch, tmp_path):
    module = installer()
    monkeypatch.setattr(module.urllib.request, 'urlopen', lambda *args, **kwargs: io.BytesIO(b'example'))
    monkeypatch.setattr(module.time, 'sleep', lambda _: None)
    spec = {'url': 'https://example.invalid/test.bin', 'sha256': hashlib.sha256(b'example').hexdigest()}
    assert module.acquire(spec, tmp_path).read_bytes() == b'example'
    spec['sha256'] = '0' * 64
    with pytest.raises(RuntimeError, match='校验失败'):
        module.acquire(spec, tmp_path / 'bad')
    assert not (tmp_path / 'bad/test.bin').exists()


def test_interrupted_download_retries_without_replacing_cached_file(monkeypatch, tmp_path):
    module = installer()
    cached = tmp_path / 'asset.bin'
    cached.write_bytes(b'old invalid cache')
    attempts = []
    def fetch(*args, **kwargs):
        attempts.append(cached.read_bytes())
        if len(attempts) == 1:
            raise OSError('simulated network interruption')
        return io.BytesIO(b'valid asset')
    monkeypatch.setattr(module.urllib.request, 'urlopen', fetch)
    monkeypatch.setattr(module.time, 'sleep', lambda _: None)
    spec = {'url': 'https://example.invalid/asset.bin', 'sha256': hashlib.sha256(b'valid asset').hexdigest()}
    assert module.acquire(spec, tmp_path).read_bytes() == b'valid asset'
    assert attempts == [b'old invalid cache', b'old invalid cache']


def test_download_failure_preserves_existing_cache(monkeypatch, tmp_path):
    module = installer()
    cached = tmp_path / 'asset.bin'
    cached.write_bytes(b'old invalid cache')
    monkeypatch.setattr(module.urllib.request, 'urlopen', lambda *args, **kwargs: io.BytesIO(b'bad data'))
    monkeypatch.setattr(module.time, 'sleep', lambda _: None)
    spec = {'url': 'https://example.invalid/asset.bin', 'sha256': hashlib.sha256(b'valid asset').hexdigest()}
    with pytest.raises(RuntimeError, match='校验失败'):
        module.acquire(spec, tmp_path)
    assert cached.read_bytes() == b'old invalid cache'
