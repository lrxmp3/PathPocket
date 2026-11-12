import hashlib
import json
from pathlib import Path

from pathpocket_gui import __version__ as gui_version
from pathpocket import __version__ as backend_version

ROOT = Path(__file__).resolve().parents[1]


def test_candidate_and_backend_versions_are_distinct():
    manifest = json.loads((ROOT / 'distribution/linux/release_manifest.json').read_text())
    assert (ROOT / 'VERSION').read_text().strip() == gui_version == '1.0.7'
    assert manifest['distribution_version'] == manifest['GUI']['version'] == gui_version
    assert manifest['backend']['version'] == backend_version == '0.3.0'


def test_gui_manifest_hashes_match_current_source():
    manifest = json.loads((ROOT / 'distribution/linux/release_manifest.json').read_text())
    for name, expected in manifest['GUI']['source_sha256'].items():
        assert hashlib.sha256((ROOT / name).read_bytes()).hexdigest() == expected, name
    expected = manifest['distribution_tools']['Create_Shortcuts.sh']
    assert hashlib.sha256((ROOT / 'distribution/linux/Create_Shortcuts.sh').read_bytes()).hexdigest() == expected


def test_molecule_count_label_handles_single_plural_and_missing():
    from pathpocket_gui.ux_i18n import tr
    assert tr('contains', 'en', n=1) == 'Molecules: 1'
    assert tr('contains', 'en', n=2) == 'Molecules: 2'
    assert tr('contains', 'en', n='NA') == 'Molecules: NA'
    assert tr('contains', 'zh', n=1) == '包含 1 个分子'
    assert tr('files', 'en') == 'Files and Provenance'
