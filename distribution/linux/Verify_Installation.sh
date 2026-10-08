#!/usr/bin/env bash
set -euo pipefail
B="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
trap 'echo "验证失败。请查看用户项目目录中的 diagnostics 和最新 run 日志。"' ERR
"$B/bin/pathpocket" doctor
if test "${1:-}" = --smoke; then
 echo '即将执行 HSA 1×10 分子测试。输入 YES 确认：'
 read -r answer
 test "$answer" = YES || exit 0
 "$B/bin/pathpocket" smoke HSA
fi
echo 'PathPocket installation verification: PASS'
