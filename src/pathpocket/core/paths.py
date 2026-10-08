"""Resolve paths once and enforce an explicit workspace capability."""
import os
import re
from pathlib import Path, PureWindowsPath

def windows_to_wsl(value):
    text = str(value).replace('\\', '/')
    if re.match(r'^[A-Za-z]:/', text):
        return '/mnt/' + text[0].lower() + '/' + text[3:]
    return text

def wsl_to_windows(value):
    text = str(value)
    match = re.match(r'^/mnt/([a-z])(?:/(.*))?$', text)
    return str(PureWindowsPath(match[1].upper() + ':/' + (match[2] or ''))) if match else text

def native_path(value, base=None):
    text = windows_to_wsl(value) if os.name != 'nt' else wsl_to_windows(value)
    path = Path(text).expanduser()
    return ((Path(base) / path) if base and not path.is_absolute() else path).resolve()

def within(path, root):
    return native_path(path).is_relative_to(native_path(root))

def guard_write(path, allowed_root):
    path, root = native_path(path), native_path(allowed_root)
    if not path.is_relative_to(root):
        raise ValueError(f'Write blocked outside authorized directory: {path}')
    return path

def safe_id(value):
    if not isinstance(value, str) or not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_-]{0,79}', value):
        raise ValueError(f'Unsafe identifier: {value!r}; use letters, digits, underscore or hyphen')
    return value
