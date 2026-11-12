"""Embed build provenance without changing source files or external engines."""
import json,os,re,subprocess
from pathlib import Path
from setuptools import setup
from setuptools.command.build_py import build_py

class BuildWithProvenance(build_py):
    def run(self):
        super().run()
        root=Path(__file__).parent
        commit=os.environ.get('PATHPOCKET_BUILD_COMMIT')
        if commit is None:
            commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=root,text=True).strip()
        if not re.fullmatch(r'[0-9a-f]{40}',commit):
            raise ValueError('Invalid PathPocket source commit')
        (Path(self.build_lib)/'pathpocket/_build_info.json').write_text(json.dumps({'git_commit':commit,'version':self.distribution.get_version()}))

setup(cmdclass={'build_py':BuildWithProvenance})
