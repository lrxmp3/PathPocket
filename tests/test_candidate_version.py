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
