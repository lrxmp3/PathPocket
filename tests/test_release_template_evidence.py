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
