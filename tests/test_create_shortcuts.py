import os
import subprocess
from pathlib import Path


def test_shortcut_creator_uses_current_package_and_user_home(tmp_path):
    source=Path(__file__).resolve().parents[1]/'Create_Shortcuts.sh'
    package=tmp_path/'Install Folder'/source.name
    package.parent.mkdir()
    package.write_bytes(source.read_bytes())
    (package.parent/'PathPocket.sh').write_text('#!/usr/bin/env bash\n')
    home=tmp_path/'用户目录'
    (home/'Desktop').mkdir(parents=True)
    env={**os.environ,'HOME':str(home),'XDG_DATA_HOME':str(home/'app data'),'PATH':'/usr/bin:/bin'}
    subprocess.run(['bash',str(package)],env=env,check=True,capture_output=True,text=True)
    desktop=home/'Desktop/PathPocket-v1.0.6.desktop'
    app=home/'app data/applications/pathpocket-v1.0.6.desktop'
    assert desktop.is_file() and os.access(desktop,os.X_OK)
    assert app.is_file() and os.access(app,os.X_OK)
    assert f'Exec="{package.parent}/PathPocket.sh"' in desktop.read_text()
    assert '/home/lrx' not in desktop.read_text()
