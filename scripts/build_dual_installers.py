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
LINUX_NAME = "PathPocket_v1.0.6_Linux"
WINDOWS_NAME = "PathPocket_v1.0.6_Windows"


def digest(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def copy_file(source: Path, target: Path) -> None:
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, target)


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


def build_wheel(destination: Path) -> Path:
    destination.mkdir(parents=True, exist_ok=True)
    subprocess.run(
        [sys.executable, "-m", "pip", "wheel", "--no-deps", "--no-build-isolation", "-w", str(destination), str(ROOT)],
        check=True,
    )
    wheels = sorted(destination.glob("pathpocket-0.3.0-*.whl"))
    if len(wheels) != 1:
        raise RuntimeError(f"expected one backend wheel, found {wheels}")
    return wheels[0]


def build(args: argparse.Namespace) -> None:
    source_sha = subprocess.check_output(["git", "-C", str(ROOT), "rev-parse", "HEAD"], text=True).strip()
    if subprocess.check_output(["git", "-C", str(ROOT), "status", "--porcelain"], text=True).strip():
        raise RuntimeError("refusing to build from a dirty source tree")
    output = args.output.resolve()
    if output.exists():
        raise RuntimeError(f"output already exists: {output}")
    output.mkdir(parents=True)

    with tempfile.TemporaryDirectory(prefix="pathpocket-build-") as temp_name:
        temp = Path(temp_name)
        linux = temp / LINUX_NAME
        shutil.copytree(args.linux_template.resolve(), linux, symlinks=True)
        assert_clean_template(linux)

        shutil.rmtree(linux / "gui" / "pathpocket_gui")
        shutil.copytree(ROOT / "gui" / "pathpocket_gui", linux / "gui" / "pathpocket_gui")
        wheel = build_wheel(temp / "wheel")
        for old in (linux / "payload" / "backend").glob("pathpocket-*.whl"):
            old.unlink()
        copy_file(wheel, linux / "payload" / "backend" / wheel.name)
        for source in (ROOT / "distribution" / "linux").iterdir():
            if source.is_file():
                copy_file(source, linux / source.name)
        copy_file(ROOT / "docs" / "INSTALL_LINUX_EN.md", linux / "docs" / "INSTALL_LINUX_EN.md")
        copy_file(ROOT / "docs" / "INSTALL_LINUX_ZH.md", linux / "docs" / "INSTALL_LINUX_ZH.md")
        copy_file(ROOT / "KNOWN_ISSUES.md", linux / "docs" / "KNOWN_ISSUES.md")
        manifest_path = linux / "release_manifest.json"
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        manifest["candidate_source_commit"] = source_sha
        manifest["installation_routes"] = ["direct Linux", "Windows 11 through Ubuntu 24.04 on WSL2/WSLg"]
        manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        for name in ("Setup_First_Run.sh", "PathPocket.sh", "Verify_Installation.sh", "Verify_Package.sh", "Create_Shortcuts.sh"):
            path = linux / name
            path.chmod(path.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)
        make_checksums(linux)

        linux_archive = output / "PathPocket_v1.0.6_Linux.tar.gz"
        with tarfile.open(linux_archive, "w:gz", dereference=False) as archive:
            archive.add(linux, arcname=LINUX_NAME, recursive=True)

        windows = temp / WINDOWS_NAME
        shutil.copytree(args.windows_template.resolve(), windows)
        for source in (ROOT / "distribution" / "windows").iterdir():
            if source.is_file():
                copy_file(source, windows / source.name)
        copy_file(ROOT / "docs" / "INSTALL_WINDOWS_ZH.md", windows / "INSTALL_WINDOWS_CN.md")
        copy_file(ROOT / "docs" / "INSTALL_WINDOWS_EN.md", windows / "INSTALL_WINDOWS_EN.md")
        copy_file(ROOT / "KNOWN_ISSUES.md", windows / "KNOWN_ISSUES.md")
        runtime = windows / "linux-runtime.tar.gz"
        shutil.copy2(linux_archive, runtime)
        setup = windows / "Setup_First_Run.ps1"
        setup_text = setup.read_text(encoding="utf-8-sig")
        if "__RUNTIME_SHA256__" not in setup_text:
            raise RuntimeError("Setup_First_Run.ps1 runtime hash placeholder is missing")
        setup.write_text(setup_text.replace("__RUNTIME_SHA256__", digest(runtime)), encoding="utf-8-sig")
        (windows / "BUILD_STATUS.txt").write_text(
            "PathPocket v1.0.6 Linux / Windows (WSL2) pre-release candidate\n"
            f"source_commit={source_sha}\n"
            "windows_native=false\nvalidation=REQUIRES_EXTERNAL_RETEST\n",
            encoding="utf-8",
        )
        make_checksums(windows)
        windows_archive = output / "PathPocket_v1.0.6_Windows.zip"
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
        "PRERELEASE_NOTES_DRAFT.md", "THIRD_PARTY_RELEASE_AUDIT.md", "VALIDATION_LINUX.md",
        "VALIDATION_WINDOWS_WSL2.md",
    ):
        copy_file(ROOT / "docs" / document, output / document)
    copy_file(ROOT / "KNOWN_ISSUES.md", output / "KNOWN_ISSUES.md")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--linux-template", type=Path, required=True)
    parser.add_argument("--windows-template", type=Path, required=True)
    parser.add_argument("--linux-template-sha256", required=True)
    parser.add_argument("--windows-template-sha256", required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    build(args)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
