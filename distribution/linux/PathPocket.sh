#!/usr/bin/env bash
set -euo pipefail
B="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
R="${PATHPOCKET_RUNTIME_ROOT:-$B}"
if ! test -x "$R/runtime/env/bin/python" && test -x /opt/pathpocket/runtime/env/bin/python; then R=/opt/pathpocket; fi
if ! test -x "$R/runtime/env/bin/python"; then echo 'PathPocket runtime unavailable. Run Setup_First_Run.sh first.'; exit 1; fi
unset PYTHONPATH PYTHONHOME CONDA_PREFIX CONDA_DEFAULT_ENV
export PYTHONNOUSERSITE=1 PYTHONDONTWRITEBYTECODE=1
export PATHPOCKET_FRONTEND_BUNDLE="$B" PATHPOCKET_RUNTIME_ROOT="$R" PATHPOCKET_LAUNCHER="$R/bin/pathpocket" PATHPOCKET_RUNTIME_PYTHON="$R/runtime/env/bin/python"
export PATHPOCKET_USER_HOME="${PATHPOCKET_USER_HOME:-$HOME/PathPocket_Projects}"
exec "$R/runtime/env/bin/python" -B "$B/gui_entry.py" "$@"
