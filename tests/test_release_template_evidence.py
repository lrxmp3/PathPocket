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
