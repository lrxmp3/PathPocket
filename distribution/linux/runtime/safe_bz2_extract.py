#!/usr/bin/env python3
"""Extract a hash-verified bzip2 tar archive without relying on system bzip2."""

from __future__ import annotations

import tarfile
from pathlib import Path
import sys


def _inside(path: Path, root: Path) -> bool:
    try:
        path.relative_to(root)
    except ValueError:
        return False
    return True


def _validate_member(member: tarfile.TarInfo, target: Path) -> None:
    destination = (target / member.name).resolve()
    if not _inside(destination, target):
        raise ValueError("Unsafe archive member: " + member.name)
    if member.isdev() or member.isfifo():
        raise ValueError("Unsupported archive member type: " + member.name)
    if member.issym() or member.islnk():
        base = destination.parent if member.issym() else target
        linked = (base / member.linkname).resolve()
        if not _inside(linked, target):
            raise ValueError("Unsafe archive link: " + member.name)


def extract(archive_path: Path, target_path: Path) -> None:
    archive = archive_path.resolve()
    target = target_path.resolve()
    if not archive.is_file():
        raise FileNotFoundError(str(archive))
    target.mkdir(parents=True, exist_ok=True)
    with tarfile.open(archive, "r:bz2") as bundle:
        members = bundle.getmembers()
        for member in members:
            _validate_member(member, target)
        bundle.extractall(target, members=members)


def main(argv: list[str]) -> int:
    if len(argv) != 3:
        raise SystemExit("usage: safe_bz2_extract.py <archive.tar.bz2> <target-directory>")
    extract(Path(argv[1]), Path(argv[2]))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
