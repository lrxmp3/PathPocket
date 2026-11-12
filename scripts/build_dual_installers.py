#!/usr/bin/env python3
"""Rebuild Linux and Windows/WSL2 installers from one source commit.

The approved Linux and Windows package templates supply unchanged v1.0.6 assets
that are not stored in Git (demo inputs, engine source, fonts and transport
helpers). Current Git GUI/backend/installer sources are overlaid and every
result is re-hashed. A preinstalled runtime and model weights are never copied.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import stat
import subprocess
import sys
import tarfile
import tempfile
import zipfile


ROOT = Path(__file__).resolve().parents[1]
LINUX_NAME = "PathPocket_v1.0.7_Linux"
WINDOWS_NAME = "PathPocket_v1.0.7_Windows"


def digest(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def template_digest(root: Path) -> str:
    """Hash a template tree, including paths, modes and internal symlinks.

    The SHA256 covers compact UTF-8 JSON records in sorted relative-path order.
    Links outside the tree, dangling links and special files are rejected.
    """
    root = root.resolve(strict=True)
    if not root.is_dir():
        raise ValueError(f"template is not a directory: {root}")
    records = []
    for path in sorted(root.rglob('*'), key=lambda p: p.relative_to(root).as_posix()):
        relative = path.relative_to(root).as_posix()
        mode = path.lstat().st_mode
        if stat.S_ISLNK(mode):
            target = os.readlink(path)
            resolved = path.resolve(strict=True)
            if not resolved.is_relative_to(root):
                raise ValueError(f"template symlink escapes root: {relative}")
            records.append([relative, 'link', target])
        elif stat.S_ISDIR(mode):
            records.append([relative, 'directory', stat.S_IMODE(mode)])
        elif stat.S_ISREG(mode):
            records.append([relative, 'file', stat.S_IMODE(mode), digest(path)])
        else:
            raise ValueError(f"unsupported template entry: {relative}")
    payload = json.dumps(records, ensure_ascii=False, separators=(',', ':')).encode('utf-8')
    return hashlib.sha256(payload).hexdigest()


def verify_template(root: Path, expected: str) -> None:
    actual = template_digest(root)
    if len(expected) != 64 or any(c not in '0123456789abcdef' for c in expected):
        raise ValueError('template SHA256 must be 64 lowercase hexadecimal characters')
    if actual != expected:
        raise ValueError(f'template SHA256 mismatch: {root}; expected {expected}, got {actual}')


def copy_file(source: Path, target: Path) -> None:
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, target)


def copy_release_notices(target: Path) -> None:
    copy_file(ROOT / "LICENSE", target / "LICENSE")
    copy_file(ROOT / "THIRD_PARTY_NOTICES.md", target / "THIRD_PARTY_NOTICES.md")
    licenses = target / "LICENSES"
    if licenses.exists():
        shutil.rmtree(licenses)
    shutil.copytree(ROOT / "LICENSES", licenses)


def make_checksums(root: Path) -> None:
    output = root / "SHA256SUMS.txt"
    rows = []
    for path in sorted(root.rglob("*")):
        if path.is_file() and path != output and "diagnostics" not in path.parts:
            rows.append(f"{digest(path)}  ./{path.relative_to(root).as_posix()}")
    output.write_text("\n".join(rows) + "\n", encoding="utf-8")


def assert_clean_template(root: Path) -> None:
    forbidden = [root / "runtime" / "bin", root / "weights", root / "payload" / "engine" / "weights"]
    present = [str(path) for path in forbidden if path.exists()]
    if present:
        raise RuntimeError("template contains installed runtime/weights: " + ", ".join(present))
    restricted_names = {'smina.static', 'weights.zip', 'GPPM.pth', 'TAPM.pth', 'Pocket2ED.pt'}
    weights_lock = json.loads((ROOT / 'distribution/linux/weights-lock.json').read_text(encoding='utf-8'))
    download_lock = json.loads((ROOT / 'distribution/linux/download-lock.json').read_text(encoding='utf-8'))
    restricted_hashes = {weights_lock['archive_sha256'], *weights_lock['weights'].values(), download_lock['smina']['sha256']}
    restricted = [p for p in root.rglob('*') if p.is_file() and
                  (p.name in restricted_names or digest(p) in restricted_hashes)]
    if restricted:
        raise RuntimeError('template contains restricted model/binary assets: ' + ', '.join(map(str, restricted)))
    # A filename/hash scan cannot see restricted files or evidence inside an
    # archive. Reject nested archives instead of claiming their contents were
    # checked. The old backend wheel is the sole exception: build() removes
    # every matching wheel and replaces it with one built from this source.
    for path in root.rglob('*'):
        if not path.is_file():
            continue
        relative = path.relative_to(root)
        if relative.parent.as_posix() == 'payload/backend' and path.match('pathpocket-*.whl'):
            continue
        with path.open('rb') as stream:
            magic = stream.read(8)
        compressed = (magic.startswith((b'PK\x03\x04', b'PK\x05\x06', b'PK\x07\x08',
                                         b'\x1f\x8b', b'BZh', b'\xfd7zXZ\x00',
                                         b'7z\xbc\xaf\x27\x1c', b'Rar!\x1a\x07'))
                      or tarfile.is_tarfile(path))
        if compressed:
            raise RuntimeError(f'template contains unreviewed nested archive: {relative}')
    # Do not silently carry historical test evidence into a new release.
    evidence = [p for p in root.rglob("*") if p.is_file() and
                ("VALIDATION" in p.name.upper() or "ACCEPTANCE" in p.name.upper()
                 or "AUDIT" in p.name.upper() or p.name.lower().endswith("_report.md")
                 or p.name.lower() == "reference_summary.json" or p.suffix.lower() in {".png", ".log", ".pyc"}
                 or any(part.lower() in {"diagnostics", "__pycache__", ".pytest_cache"} for part in p.relative_to(root).parts))]
    if evidence:
        raise RuntimeError("template contains local validation evidence: " + ", ".join(map(str, evidence)))


def build_wheel(destination: Path, source_sha: str) -> Path:
    destination.mkdir(parents=True, exist_ok=True)
    # Build only from the selected tracked commit, not ignored or untracked
    # files (or stale build products) in the developer's working directory.
    with tempfile.TemporaryDirectory(prefix='pathpocket-wheel-source-') as temp_name:
        source = Path(temp_name) / 'source'
        source.mkdir()
        snapshot = Path(temp_name) / 'source.tar'
        subprocess.run(['git', '-C', str(ROOT), 'archive', '--format=tar',
                        '--output', str(snapshot), source_sha], check=True)
        with tarfile.open(snapshot, 'r:') as archive:
            archive.extractall(source, filter='data')
        subprocess.run(
            [sys.executable, "-m", "pip", "wheel", "--no-deps", "--no-build-isolation", "-w", str(destination), str(source)],
            check=True, env={**os.environ, "PATHPOCKET_BUILD_COMMIT": source_sha},
        )
    wheels = sorted(destination.glob("pathpocket-0.3.0-*.whl"))
    if len(wheels) != 1:
        raise RuntimeError(f"expected one backend wheel, found {wheels}")
    return wheels[0]


def assert_no_ignored_source_files(root: Path) -> None:
    # The GUI and license directories are copied from the worktree.  Git's
    # ordinary status omits ignored files, which must not be packaged silently.
    ignored = subprocess.check_output(
        ['git', '-C', str(root), 'ls-files', '--others', '--ignored', '--exclude-standard', '-z']
    )
    if ignored:
        raise RuntimeError('refusing to build with Git-ignored files in the worktree; use a clean isolated checkout')


def build(args: argparse.Namespace) -> None:
    source_sha = subprocess.check_output(["git", "-C", str(ROOT), "rev-parse", "HEAD"], text=True).strip()
    if subprocess.check_output(["git", "-C", str(ROOT), "status", "--porcelain"], text=True).strip():
        raise RuntimeError("refusing to build from a dirty source tree")
    assert_no_ignored_source_files(ROOT)
    verify_template(args.linux_template, args.linux_template_sha256)
    verify_template(args.windows_template, args.windows_template_sha256)
    output = args.output.resolve()
    if output.exists():
        raise RuntimeError(f"output already exists: {output}")
    output.mkdir(parents=True)

    with tempfile.TemporaryDirectory(prefix="pathpocket-build-") as temp_name:
        temp = Path(temp_name)
        linux = temp / LINUX_NAME
        shutil.copytree(args.linux_template.resolve(), linux, symlinks=True)
        verify_template(linux, args.linux_template_sha256)
        assert_clean_template(linux)

        shutil.rmtree(linux / "gui" / "pathpocket_gui")
        shutil.copytree(
            ROOT / "gui" / "pathpocket_gui",
            linux / "gui" / "pathpocket_gui",
            ignore=shutil.ignore_patterns("__pycache__", "*.pyc", "*.pyo"),
        )
        wheel = build_wheel(temp / "wheel", source_sha)
        for old in (linux / "payload" / "backend").glob("pathpocket-*.whl"):
            old.unlink()
        copy_file(wheel, linux / "payload" / "backend" / wheel.name)
        for source in (ROOT / "distribution" / "linux").iterdir():
            if source.is_file():
                copy_file(source, linux / source.name)
        copy_file(ROOT / "docs" / "INSTALL_LINUX_EN.md", linux / "docs" / "INSTALL_LINUX_EN.md")
        copy_file(ROOT / "docs" / "INSTALL_LINUX_ZH.md", linux / "docs" / "INSTALL_LINUX_ZH.md")
        copy_file(ROOT / "KNOWN_ISSUES.md", linux / "docs" / "KNOWN_ISSUES.md")
        copy_file(ROOT / "RELEASE_NOTES_v1.0.7.md", linux / "RELEASE_NOTES_v1.0.7.md")
        for demo in (ROOT / "examples" / "fixtures").iterdir():
            if (demo / "README_FIRST.txt").is_file() and (linux / "payload" / "demos" / demo.name).is_dir():
                copy_file(demo / "README_FIRST.txt", linux / "payload" / "demos" / demo.name / "README_FIRST.txt")
        copy_release_notices(linux)
        copy_file(ROOT / "tests" / "test_wsl_windows_open.py", linux / "tests" / "test_wsl_windows_open.py")
        manifest_path = linux / "release_manifest.json"
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        manifest["candidate_source_commit"] = source_sha
        manifest["installation_routes"] = ["direct Linux", "Windows 11 through Ubuntu 24.04 on WSL2/WSLg"]
        manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        for name in ("Setup_First_Run.sh", "PathPocket.sh", "Verify_Installation.sh", "Verify_Package.sh", "Create_Shortcuts.sh"):
            path = linux / name
            path.chmod(path.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)
        make_checksums(linux)

        linux_archive = output / "PathPocket_v1.0.7_Linux.tar.gz"
        with tarfile.open(linux_archive, "w:gz", dereference=False) as archive:
            archive.add(linux, arcname=LINUX_NAME, recursive=True)

        windows = temp / WINDOWS_NAME
        shutil.copytree(args.windows_template.resolve(), windows, symlinks=True)
        verify_template(windows, args.windows_template_sha256)
        assert_clean_template(windows)
        for source in (ROOT / "distribution" / "windows").iterdir():
            if source.is_file():
                copy_file(source, windows / source.name)
        copy_file(ROOT / "docs" / "INSTALL_WINDOWS_ZH.md", windows / "INSTALL_WINDOWS_CN.md")
        copy_file(ROOT / "docs" / "INSTALL_WINDOWS_EN.md", windows / "INSTALL_WINDOWS_EN.md")
        copy_file(ROOT / "KNOWN_ISSUES.md", windows / "KNOWN_ISSUES.md")
        copy_release_notices(windows)
        runtime = windows / "linux-runtime.tar.gz"
        shutil.copy2(linux_archive, runtime)
        setup = windows / "Setup_First_Run.ps1"
        setup_text = setup.read_text(encoding="utf-8-sig")
        if "__RUNTIME_SHA256__" not in setup_text:
            raise RuntimeError("Setup_First_Run.ps1 runtime hash placeholder is missing")
        setup.write_text(setup_text.replace("__RUNTIME_SHA256__", digest(runtime)), encoding="utf-8-sig")
        (windows / "BUILD_STATUS.txt").write_text(
            "PathPocket v1.0.7 Linux / Windows (WSL2) pre-release candidate\n"
            f"source_commit={source_sha}\n"
            "windows_native=false\nvalidation=REQUIRES_EXTERNAL_RETEST\n",
            encoding="utf-8",
        )
        make_checksums(windows)
        windows_archive = output / "PathPocket_v1.0.7_Windows.zip"
        with zipfile.ZipFile(windows_archive, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
            for path in sorted(windows.rglob("*")):
                if path.is_file():
                    archive.write(path, (Path(WINDOWS_NAME) / path.relative_to(windows)).as_posix())

    sums = output / "SHA256SUMS.txt"
    sums.write_text(
        f"{digest(linux_archive)}  {linux_archive.name}\n"
        f"{digest(windows_archive)}  {windows_archive.name}\n",
        encoding="utf-8",
    )
    (output / "SOURCE_ASSET_MAPPING.txt").write_text(
        f"source_commit={source_sha}\n"
        f"linux={linux_archive.name} sha256={digest(linux_archive)}\n"
        f"windows={windows_archive.name} sha256={digest(windows_archive)}\n"
        f"linux_template_sha256={args.linux_template_sha256}\n"
        f"windows_template_sha256={args.windows_template_sha256}\n",
        encoding="utf-8",
    )
    for document in (
        "INSTALL_LINUX_EN.md", "INSTALL_LINUX_ZH.md", "INSTALL_WINDOWS_EN.md", "INSTALL_WINDOWS_ZH.md",
        "THIRD_PARTY_RELEASE_AUDIT.md",
    ):
        copy_file(ROOT / "docs" / document, output / document)
    copy_file(ROOT / "KNOWN_ISSUES.md", output / "KNOWN_ISSUES.md")
    copy_release_notices(output)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--linux-template", type=Path, required=True)
    parser.add_argument("--windows-template", type=Path, required=True)
    parser.add_argument("--linux-template-sha256", required=True, help="SHA256 of the template directory from template_digest(), not the original archive")
    parser.add_argument("--windows-template-sha256", required=True, help="SHA256 of the template directory from template_digest(), not the original archive")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    build(args)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
