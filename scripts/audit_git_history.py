#!/usr/bin/env python3
"""Offline, non-secret-printing release audit for all reachable Git blobs."""

from __future__ import annotations

import argparse
import re
import subprocess
from pathlib import Path


PATTERNS = {
    "PRIVATE_KEY": re.compile(rb"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"),
    "GITHUB_TOKEN": re.compile(rb"gh[pousr]_[A-Za-z0-9_]{20,}"),
    "AWS_ACCESS_KEY": re.compile(rb"AKIA[0-9A-Z]{16}"),
    "OPENAI_KEY": re.compile(rb"sk-(?:proj-)?[A-Za-z0-9_-]{20,}"),
    "PASSWORD_ASSIGNMENT": re.compile(rb"(?i)(?:password|passwd|secret)\s*[:=]\s*[^\s$<{][^\r\n]{7,}"),
    "PRIVATE_LINUX_PATH": re.compile(rb"/(?:home|media)/lrx(?:/|\\)"),
    "BN_CL": re.compile(rb"(?i)Bn[-_ ]?Cl|benzyl\s+chloride"),
}

FORBIDDEN_PATH = re.compile(
    r"(?i)(^|/)(?:evidence|runs?|results?|diagnostics)(/|$)|\.(?:zip|7z|rar|tar\.gz|tgz|pth|pt)$"
)


def git(repo: Path, *args: str, text: bool = False):
    return subprocess.check_output(["git", "-C", str(repo), *args], text=text)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", type=Path, default=Path.cwd())
    parser.add_argument("--large-bytes", type=int, default=10 * 1024 * 1024)
    args = parser.parse_args()
    repo = args.repo.resolve()
    lines = git(repo, "rev-list", "--objects", "--all", text=True).splitlines()
    findings: list[tuple[str, str, str]] = []
    scanned = 0
    seen: set[str] = set()
    for line in lines:
        oid, _, path = line.partition(" ")
        if oid in seen:
            continue
        seen.add(oid)
        if git(repo, "cat-file", "-t", oid, text=True).strip() != "blob":
            continue
        scanned += 1
        size = int(git(repo, "cat-file", "-s", oid, text=True).strip())
        display = path or "<unresolved-path>"
        if size > args.large_bytes:
            findings.append(("LARGE_BLOB", display, f"{size} bytes"))
        if path and FORBIDDEN_PATH.search(path):
            findings.append(("FORBIDDEN_PATH", display, "path policy match"))
        if size > 25 * 1024 * 1024:
            continue
        data = git(repo, "cat-file", "blob", oid)
        for name, pattern in PATTERNS.items():
            if pattern.search(data):
                findings.append((name, display, f"blob {oid[:12]}"))

    print(f"AUDIT_TOOL=PathPocket offline history audit v1")
    print(f"REPOSITORY={repo}")
    print("SCOPE=git rev-list --objects --all (all reachable refs)")
    print(f"BLOBS_SCANNED={scanned}")
    print(f"FINDINGS={len(findings)}")
    for kind, path, detail in sorted(findings):
        print(f"{kind}\t{path}\t{detail}")
    return 1 if findings else 0


if __name__ == "__main__":
    raise SystemExit(main())
