"""Static source contracts for the Windows/WSL2 installer remediation.

Real UAC, WSL and WSLg behaviour is covered by the external Windows validation
template; these checks prevent the known implementation regressions from returning.
"""

from pathlib import Path


ROOT=Path(__file__).resolve().parents[1]
WINDOWS=ROOT/'distribution'/'windows'
LINUX=ROOT/'distribution'/'linux'


def test_wsl_state_transitions_are_visible_and_resumable():
    text=(WINDOWS/'Setup_First_Run.ps1').read_text(encoding='utf-8-sig')
    for state in ['A_NO_WSL','B_NO_DISTRO','C_DISTRO_NOT_WSL2','D_READY','E_INITIALIZATION_REQUIRED']:
        assert state in text
    assert 'Invoke-WslLogged @("--install", "-d", $Distro)' in text
    assert 'Invoke-WslSilent @("--install", "-d", $Distro)' not in text
    assert 'Invoke-WslLogged @("--set-version", $Distro, "2")' in text
    assert 'INSTALL_IN_PROGRESS' in text
    assert 'RESTART_REQUIRED' in text and 'INITIALIZATION_REQUIRED' in text and 'exit 20' in text
    assert 'getent passwd 1000' in text


def test_gpu_probe_uses_safe_official_wsl_fallback():
    text=(WINDOWS/'Setup_First_Run.ps1').read_text(encoding='utf-8-sig')
    assert 'Invoke-WslLogged @("-d", $Distro, "--", "nvidia-smi")' in text
    assert 'Invoke-WslLogged @("-d", $Distro, "--", "/usr/lib/wsl/lib/nvidia-smi")' in text
    assert 'GPU_AVAILABLE_VIA_WSL_SHIM' in text
    assert 'GPU_UNAVAILABLE' in text
    assert 'apt-get' not in text and 'ln -s' not in text


def test_paths_logs_and_hash_guard_are_portable():
    ps=(WINDOWS/'Setup_First_Run.ps1').read_text(encoding='utf-8-sig')
    assert 'System.Security.Cryptography.SHA256' in ps
    assert 'Get-FileHash' not in ps
    assert 'UTF8Encoding($false)' in ps and 'AppendAllText' in ps and 'Tee-Object' not in ps
    assert '--cd' in ps and '$PackageRoot' in ps and 'wslpath' not in ps and '.Replace("C:' not in ps
    assert 'System32\\WindowsPowerShell\\v1.0\\powershell.exe' in ps
    for name in ['Setup_First_Run.bat','Test_Package_Preflight.bat','Launch_PathPocket.bat','Create_Desktop_Shortcut.bat']:
        content=(WINDOWS/name).read_text(encoding='ascii')
        assert '%SystemRoot%\\System32\\WindowsPowerShell\\v1.0\\powershell.exe' in content
        assert 'DisableDelayedExpansion' in content


def test_fresh_ubuntu_bzip2_fallback_is_packaged_source_not_system_mutation():
    setup=(LINUX/'Setup_First_Run.sh').read_text(encoding='utf-8')
    helper=LINUX/'runtime'/'safe_bz2_extract.py'
    assert 'command -v bzip2' in setup
    assert 'safe_bz2_extract.py' in setup
    assert 'apt-get' not in setup
    assert helper.is_file()
    helper_text=helper.read_text(encoding='utf-8')
    assert 'Unsafe archive member' in helper_text and 'Unsafe archive link' in helper_text
