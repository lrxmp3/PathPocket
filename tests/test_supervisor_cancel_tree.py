import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import time


def test_cancel_stops_detached_descendant_and_not_unrelated_process(tmp_path):
    root = Path(__file__).resolve().parents[1]
    session = tmp_path / 'session'
    session.mkdir()
    project = tmp_path / 'project'
    project.mkdir()
    child_file = tmp_path / 'child.pid'
    launcher = tmp_path / 'launcher.py'
    launcher.write_text('#!' + sys.executable + '\n'
                        'import subprocess,sys\nfrom pathlib import Path\n'
                        'p=subprocess.Popen([sys.executable,"-c","import time;time.sleep(40)"],start_new_session=True)\n'
                        'Path(sys.argv[2]).write_text(str(p.pid))\np.wait()\n')
    launcher.chmod(0o700)
    request = dict(workspace=str(tmp_path), project=str(project), command='run',
                   launcher=str(launcher), arguments=[str(child_file)])
    (session / 'request.json').write_text(json.dumps(request))
    unrelated = subprocess.Popen([sys.executable, '-c', 'import time;time.sleep(40)'], start_new_session=True)
    supervisor = subprocess.Popen([sys.executable, str(root / 'gui/pathpocket_gui/wsl_supervisor.py'), str(session / 'request.json')])
    child = None
    try:
        deadline = time.monotonic() + 10
        while not child_file.exists() and time.monotonic() < deadline:
            time.sleep(.05)
        assert child_file.exists()
        child = int(child_file.read_text())
        (session / 'cancel.json').write_text('{}')
        assert supervisor.wait(timeout=15) == 0
        response = json.loads((session / 'response.json').read_text())
        assert response['status'] == 'INTERRUPTED'
        assert response['cancelled_descendants_checked'] >= 1
        stat = Path('/proc') / str(child) / 'stat'
        if stat.exists():
            raw = stat.read_text()
            assert raw[raw.rfind(')') + 2:].split()[0] == 'Z'
        assert unrelated.poll() is None
    finally:
        if supervisor.poll() is None:
            supervisor.kill()
            supervisor.wait()
        if child:
            try:
                os.killpg(child, signal.SIGKILL)
            except ProcessLookupError:
                pass
        unrelated.terminate()
        unrelated.wait(timeout=5)


def test_signal_descendants_skips_reused_missing_and_zombie_pids(monkeypatch):
    import importlib.util
    root = Path(__file__).resolve().parents[1]
    spec = importlib.util.spec_from_file_location('supervisor_test', root / 'gui/pathpocket_gui/wsl_supervisor.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    identities = {101: 'old', 102: 'gone', 103: 'zombie', 104: 'same'}
    observed = {101: ('S', 1, 'new'), 102: None, 103: ('Z', 1, 'zombie'), 104: ('S', 1, 'same')}
    sent = []
    monkeypatch.setattr(module, 'process_identity', lambda pid: observed[pid])
    monkeypatch.setattr(module.os, 'kill', lambda pid, sig: sent.append((pid, sig)))
    assert module.signal_descendants(identities, signal.SIGTERM) == []
    assert sent == [(104, signal.SIGTERM)]
