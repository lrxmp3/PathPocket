import importlib.util
from pathlib import Path

import pytest


def load_builder():
    path = Path(__file__).resolve().parents[1] / 'scripts/build_dual_installers.py'
    spec = importlib.util.spec_from_file_location('release_builder', path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.mark.parametrize('name', ['VALIDATION_LINUX.md', 'screenshots.png', 'run.log', 'INTERNAL_AUDIT.md'])
def test_builder_rejects_template_evidence(tmp_path, name):
    docs = tmp_path / 'docs'
    docs.mkdir()
    (docs / name).write_text('local evidence')
    with pytest.raises(RuntimeError, match='validation evidence'):
        load_builder().assert_clean_template(tmp_path)


def test_builder_accepts_user_documents(tmp_path):
    docs = tmp_path / 'docs'
    docs.mkdir()
    (docs / 'INSTALL_LINUX_EN.md').write_text('installation instructions')
    load_builder().assert_clean_template(tmp_path)


def test_builder_rejects_diagnostics_outside_docs(tmp_path):
    diagnostics = tmp_path / 'diagnostics'
    diagnostics.mkdir()
    (diagnostics / 'run.json').write_text('{}')
    with pytest.raises(RuntimeError, match='validation evidence'):
        load_builder().assert_clean_template(tmp_path)


@pytest.mark.parametrize('name', ['smina.static', 'weights.zip', 'GPPM.pth', 'TAPM.pth', 'Pocket2ED.pt'])
def test_builder_rejects_restricted_assets(tmp_path, name):
    (tmp_path / name).write_bytes(b'fixture')
    with pytest.raises(RuntimeError, match='restricted model/binary assets'):
        load_builder().assert_clean_template(tmp_path)


def test_builder_rejects_renamed_restricted_asset(tmp_path, monkeypatch):
    builder = load_builder()
    template = tmp_path / 'template'
    template.mkdir()
    renamed = template / 'unrelated-name.bin'
    renamed.write_bytes(b'fixture')
    lock = __import__('json').loads((builder.ROOT / 'distribution/linux/weights-lock.json').read_text())
    monkeypatch.setattr(builder, 'digest', lambda path: lock['archive_sha256'])
    with pytest.raises(RuntimeError, match='restricted model/binary assets'):
        builder.assert_clean_template(template)


def test_builder_rejects_renamed_nested_archive(tmp_path):
    import zipfile
    archive = tmp_path / 'ordinary.dat'
    with zipfile.ZipFile(archive, 'w') as z:
        z.writestr('private/validation.log', 'fixture')
    with pytest.raises(RuntimeError, match='unreviewed nested archive'):
        load_builder().assert_clean_template(tmp_path)


def test_builder_permits_backend_wheel_replaced_during_build(tmp_path):
    import zipfile
    wheel = tmp_path / 'payload/backend/pathpocket-0.3.0-py3-none-any.whl'
    wheel.parent.mkdir(parents=True)
    with zipfile.ZipFile(wheel, 'w') as z:
        z.writestr('placeholder', 'fixture')
    load_builder().assert_clean_template(tmp_path)


def test_template_digest_detects_content_mode_and_link_changes(tmp_path):
    builder = load_builder()
    template = tmp_path / 'template'
    template.mkdir()
    item = template / 'file'
    item.write_text('original')
    (template / 'link').symlink_to('file')
    expected = builder.template_digest(template)
    builder.verify_template(template, expected)
    item.write_text('changed')
    with pytest.raises(ValueError, match='mismatch'):
        builder.verify_template(template, expected)
    item.write_text('original')
    item.chmod(0o755)
    with pytest.raises(ValueError, match='mismatch'):
        builder.verify_template(template, expected)


def test_template_digest_rejects_outside_and_dangling_links(tmp_path):
    builder = load_builder()
    template = tmp_path / 'template'
    template.mkdir()
    outside = tmp_path / 'outside'
    outside.write_text('data')
    link = template / 'link'
    link.symlink_to(outside)
    with pytest.raises(ValueError, match='escapes root'):
        builder.template_digest(template)
    link.unlink()
    link.symlink_to('missing')
    with pytest.raises(FileNotFoundError):
        builder.template_digest(template)


def test_template_digest_survives_copy_preserving_links_and_modes(tmp_path):
    import shutil
    builder = load_builder()
    source = tmp_path / 'source'
    source.mkdir()
    (source / 'file').write_text('data')
    (source / 'link').symlink_to('file')
    target = tmp_path / 'copy'
    shutil.copytree(source, target, symlinks=True)
    builder.verify_template(target, builder.template_digest(source))


def test_release_notices_include_candidate_license(tmp_path):
    builder = load_builder()
    (tmp_path / 'LICENSE').write_text('old template license')
    builder.copy_release_notices(tmp_path)
    assert (tmp_path / 'LICENSE').read_bytes() == (builder.ROOT / 'LICENSE').read_bytes()
    assert (tmp_path / 'THIRD_PARTY_NOTICES.md').read_bytes() == (builder.ROOT / 'THIRD_PARTY_NOTICES.md').read_bytes()
    assert (tmp_path / 'LICENSES' / 'ED2Mol-MIT.txt').is_file()
