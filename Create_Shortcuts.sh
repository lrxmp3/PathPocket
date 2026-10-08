#!/usr/bin/env bash
set -euo pipefail

PACKAGE_ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
LAUNCHER="$PACKAGE_ROOT/PathPocket.sh"
APP_DIR="${XDG_DATA_HOME:-$HOME/.local/share}/applications"

if command -v xdg-user-dir >/dev/null 2>&1; then
    DESKTOP_DIR="$(xdg-user-dir DESKTOP 2>/dev/null || true)"
else
    DESKTOP_DIR=""
fi
if [[ -z "$DESKTOP_DIR" || "$DESKTOP_DIR" == "$HOME" ]]; then
    if [[ -d "$HOME/桌面" ]]; then
        DESKTOP_DIR="$HOME/桌面"
    else
        DESKTOP_DIR="$HOME/Desktop"
    fi
fi

mkdir -p "$DESKTOP_DIR" "$APP_DIR"
DESKTOP_FILE="$DESKTOP_DIR/PathPocket-v1.0.6.desktop"
APP_FILE="$APP_DIR/pathpocket-v1.0.6.desktop"

write_entry() {
    local destination="$1"
    {
        printf '%s\n' '[Desktop Entry]'
        printf '%s\n' 'Type=Application'
        printf '%s\n' 'Name=PathPocket v1.0.6'
        printf '%s\n' 'Comment=PathPocket protein microregion workflow'
        printf 'Exec="%s"\n' "$LAUNCHER"
        printf '%s\n' 'Terminal=false'
        printf '%s\n' 'Categories=Science;'
        printf '%s\n' 'StartupNotify=true'
    } > "$destination"
    chmod 0755 "$destination"
}

write_entry "$DESKTOP_FILE"
write_entry "$APP_FILE"
if command -v gio >/dev/null 2>&1; then
    gio set "$DESKTOP_FILE" metadata::trusted true >/dev/null 2>&1 || true
fi

printf '桌面快捷方式：%s\n' "$DESKTOP_FILE"
printf '应用菜单入口：%s\n' "$APP_FILE"
printf '若桌面仍提示未信任，请右键快捷方式，选择“允许启动”。\n'
