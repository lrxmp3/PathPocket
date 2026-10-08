"""Embed build provenance without changing source files or external engines."""
import json,subprocess
from pathlib import Path
from setuptools import setup
from setuptools.command.build_py import build_py

class BuildWithProvenance(build_py):
    def run(self):
        super().run()
        root=Path(__file__).parent
        commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=root,text=True).strip()
        (Path(self.build_lib)/'pathpocket/_build_info.json').write_text(json.dumps({'git_commit':commit,'version':self.distribution.get_version()}))

setup(cmdclass={'build_py':BuildWithProvenance})
