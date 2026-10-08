#!/usr/bin/env bash
set -euo pipefail
B="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
mkdir -p "$B/diagnostics" "$B/runtime/tmp" "$B/runtime/build-home"
cd -- "$B"
PROBE="$B/runtime/tmp/case_probe_$$"
mkdir "$PROBE"
touch "$PROBE/A"
if test -e "$PROBE/a"; then
 rm -- "$PROBE/A";rmdir -- "$PROBE"
 echo '当前文件夹不支持区分文件名大小写。请将软件解压到 Linux 文件系统后重试。';exit 1
fi
rm -- "$PROBE/A";rmdir -- "$PROBE"
LOG="$B/diagnostics/setup_$(date +%Y%m%d_%H%M%S).txt"
exec > >(tee -a "$LOG") 2>&1
trap 'rc=$?; echo "安装未完成。失败命令：$BASH_COMMAND；退出码：$rc；请保留整个文件夹并重试；详细日志：$LOG"; exit "$rc"' ERR
test "$(uname -m)" = x86_64 || { echo '需要 x86_64 Linux'; exit 1; }
if test -r /etc/os-release; then
 . /etc/os-release
 echo "Linux distribution: ${PRETTY_NAME:-unknown}"
 case "${ID:-}:${VERSION_ID:-}" in ubuntu:24.04) echo 'Linux target match: Ubuntu 24.04 LTS x86_64' ;; *) echo 'UNVALIDATED_LINUX_DISTRIBUTION: 本发布目标为 Ubuntu 24.04 LTS x86_64；当前发行版未完成独立验收。' ;; esac
fi
command -v curl >/dev/null || { echo '缺少系统下载工具 curl。请联系系统管理员安装 curl 后重试。'; exit 1; }
FREE=$(df -Pk "$B" | awk 'NR==2{print $4}')
test "$FREE" -gt 40000000 || { echo '可用磁盘空间不足，需要至少40GB。'; exit 1; }
unset PYTHONPATH CONDA_PREFIX CONDA_DEFAULT_ENV PYTHONHOME
export PYTHONNOUSERSITE=1 PYTHONDONTWRITEBYTECODE=1
export MAMBA_ROOT_PREFIX="$B/runtime/mamba-root" TMPDIR="$B/runtime/tmp"
export CONDA_PKGS_DIRS="$B/runtime/mamba-root/pkgs"
mkdir -p "$B/runtime/tools"
if test ! -x "$B/runtime/tools/bin/micromamba"; then
  curl --fail --location --retry 3 --connect-timeout 30 --max-time 600 'https://conda.anaconda.org/conda-forge/linux-64/micromamba-2.9.0-0.tar.bz2' -o "$B/runtime/micromamba.tar.bz2"
  echo "8761c382127e6363bd9e0a2451aa3ef90d071a79133f736e2f759a3bf13040dd  $B/runtime/micromamba.tar.bz2" | sha256sum -c -
  tar -xjf "$B/runtime/micromamba.tar.bz2" -C "$B/runtime/tools"
fi
if test ! -f "$B/runtime/.conda-complete"; then
  MODE=create
  test ! -f "$B/runtime/env/conda-meta/history" || MODE=install
  HOME="$B/runtime/build-home" "$B/runtime/tools/bin/micromamba" "$MODE" --no-rc --always-copy -y -p "$B/runtime/env" -f "$B/conda-explicit.txt"
  touch "$B/runtime/.conda-complete"
fi
"$B/runtime/env/bin/python" -B "$B/install_runtime.py"
"$B/Verify_Installation.sh" --quick
echo 'PathPocket 安装完成。以后运行 PathPocket.sh。'
