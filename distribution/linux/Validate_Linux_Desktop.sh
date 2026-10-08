#!/usr/bin/env bash
set -euo pipefail
B="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
LOG="$B/diagnostics/linux_desktop_validation_$(date +%Y%m%d_%H%M%S).log"
mkdir -p "$B/diagnostics"
exec > >(tee -a "$LOG") 2>&1
trap 'rc=$?; echo "VALIDATION_FAIL command=$BASH_COMMAND exit_code=$rc log=$LOG"; exit "$rc"' ERR

echo "PathPocket Linux desktop validation"
echo "package_root=$B"
echo "kernel=$(uname -a)"
if grep -qi microsoft /proc/sys/kernel/osrelease 2>/dev/null; then
  echo 'INDEPENDENT_LINUX_NOT_VERIFIED: WSL is not an independent Linux desktop environment.'
  exit 2
fi
test -r /etc/os-release && cat /etc/os-release
echo "desktop=${XDG_CURRENT_DESKTOP:-unset} display=${DISPLAY:-unset} wayland=${WAYLAND_DISPLAY:-unset}"
test -n "${DISPLAY:-}${WAYLAND_DISPLAY:-}" || { echo 'No graphical desktop session detected.'; exit 3; }

cd "$B"
bash Verify_Package.sh
bash Verify_Installation.sh
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. runtime/env/bin/python -m unittest discover -s tests -v
command -v xdg-open >/dev/null || { echo 'Missing xdg-open (install xdg-utils).'; exit 4; }
command -v xdg-mime >/dev/null || { echo 'Missing xdg-mime (install xdg-utils).'; exit 4; }
echo "sdf_default=$(xdg-mime query default chemical/x-mdl-sdfile || true)"

QA_ROOT="${TMPDIR:-/tmp}/PathPocket Linux QA 中文 路径 (1)"
mkdir -p "$QA_ROOT"
test -w "$QA_ROOT"
printf 'PathPocket path probe\n' > "$QA_ROOT/path probe.txt"
test -s "$QA_ROOT/path probe.txt"

if test "${1:-}" = --smoke; then
  bash Verify_Installation.sh --smoke
fi
echo 'MANUAL_GUI_CHECK_REQUIRED: start PathPocket.sh; select input/workspace; reload the smoke result; prepare/open Chinese and English reports; open one SDF or verify the no-viewer prompt; open the result folder; close and restart; repeat from the Chinese/space path.'
echo "VALIDATION_AUTOMATED_PASS log=$LOG"
