import os
import base64
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from gui.pathpocket_gui.ux_paths import ProjectPathResolver
from gui.pathpocket_gui.ux_reports import portable_href


class WslWindowsOpenTests(unittest.TestCase):
    def setUp(self):
        self.resolver = ProjectPathResolver('Ubuntu-24.04')

    @patch.dict(os.environ, {'WSL_DISTRO_NAME': 'Ubuntu-24.04'})
    @patch('gui.pathpocket_gui.ux_paths.subprocess.run')
    def test_unicode_space_path_is_converted_without_shell(self, run):
        run.return_value = subprocess.CompletedProcess([], 0, '\\\\wsl.localhost\\Ubuntu-24.04\\home\\user\\中文 结果\\report_zh.html\n', '')
        target = self.resolver.windows_target('/home/user/中文 结果/report_zh.html')
        self.assertEqual(target, r'\\wsl.localhost\Ubuntu-24.04\home\user\中文 结果\report_zh.html')
        self.assertEqual(run.call_args.args[0][0:2], ['wslpath', '-w'])

    @patch.dict(os.environ, {'WSL_DISTRO_NAME': 'Ubuntu-24.04'})
    @patch('gui.pathpocket_gui.ux_paths.Path.exists', return_value=True)
    @patch.object(ProjectPathResolver, 'windows_target', return_value=r'\\wsl.localhost\Ubuntu-24.04\home\user\report.html')
    @patch.object(ProjectPathResolver, '_windows_shell_open')
    def test_open_uses_windows_shell_in_wsl(self, shell_open, target, exists):
        result = self.resolver.open('/home/user/report.html')
        self.assertEqual(result, target.return_value)
        shell_open.assert_called_once_with(target.return_value)

    @patch('gui.pathpocket_gui.ux_paths.Path.exists', return_value=True)
    @patch('gui.pathpocket_gui.ux_paths.subprocess.run')
    def test_windows_shell_encodes_target(self, run, exists):
        run.return_value=subprocess.CompletedProcess([],0,b'',b'')
        self.resolver._windows_shell_open(r'\\wsl.localhost\Ubuntu-24.04\home\user\中文 (1)\report.html')
        args=run.call_args.args[0]
        self.assertEqual(args[1:4],['-NoProfile','-NonInteractive','-EncodedCommand'])
        script=base64.b64decode(args[4]).decode('utf-16le')
        self.assertNotIn('中文 (1)',script)

    @patch.dict(os.environ, {}, clear=True)
    @patch.object(ProjectPathResolver, 'is_wsl', return_value=False)
    @patch('gui.pathpocket_gui.ux_paths.shutil.which', return_value='/usr/bin/xdg-mime')
    @patch('gui.pathpocket_gui.ux_paths.subprocess.run')
    def test_linux_sdf_association_uses_xdg_mime(self, run, which, is_wsl):
        run.side_effect=[
            subprocess.CompletedProcess([],0,'chemical/x-mdl-sdfile\n',''),
            subprocess.CompletedProcess([],0,'org.example.Viewer.desktop\n',''),
        ]
        self.assertTrue(self.resolver.has_default_application(Path('/tmp/molecule.sdf')))
        self.assertEqual(run.call_args_list[0].args[0][1:3],['query','filetype'])
        self.assertEqual(run.call_args_list[1].args[0][1:3],['query','default'])

    @patch.object(ProjectPathResolver, 'is_wsl', return_value=False)
    @patch('gui.pathpocket_gui.ux_paths.shutil.which', return_value=None)
    def test_linux_missing_xdg_mime_is_actionable_no_viewer(self, which, is_wsl):
        self.assertFalse(self.resolver.has_default_application(Path('/tmp/molecule.sdf')))
        self.assertFalse(self.resolver.can_choose_application())

    @patch.dict(os.environ, {'WSL_DISTRO_NAME': 'Ubuntu-24.04'})
    @patch.object(ProjectPathResolver, '_windows_executable', return_value='/mnt/c/Windows/System32/reg.exe')
    @patch('gui.pathpocket_gui.ux_paths.subprocess.run')
    def test_missing_sdf_association_is_detected(self, run, executable):
        run.return_value = subprocess.CompletedProcess([], 1, b'', b'')
        self.assertFalse(self.resolver.has_default_application(Path('/tmp/molecule.sdf')))
        self.assertEqual(run.call_count, 2)

    def test_report_links_are_relative_and_url_encoded(self):
        with tempfile.TemporaryDirectory(prefix='PathPocket 中文 ') as folder:
            root=Path(folder);report=root/'presentation'/'view';target=root/'runs'/'结果 (1).sdf'
            report.mkdir(parents=True);target.parent.mkdir();target.write_text('test',encoding='utf-8')
            href=portable_href(target,report)
            self.assertFalse(href.startswith('file:'))
            self.assertIn('%E7%BB%93%E6%9E%9C%20%281%29.sdf',href)

    def test_report_does_not_link_missing_file(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder)
            self.assertIsNone(portable_href(root/'missing.sdf',root))

    @patch('gui.pathpocket_gui.ux_paths.Path.exists')
    def test_explorer_is_found_in_windows_directory(self, exists):
        exists.return_value=True
        self.assertEqual(self.resolver._windows_executable('explorer.exe'),'/mnt/c/Windows/explorer.exe')


if __name__ == '__main__':
    unittest.main()
