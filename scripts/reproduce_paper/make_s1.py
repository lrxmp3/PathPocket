"""Restore the archived make_s1 data; this entry point does not recompute scientific results."""
from pathlib import Path
import subprocess,sys
subprocess.run([sys.executable,str(Path(__file__).with_name('materialize.py')),*sys.argv[1:],'--group','04_CORRESPONDENCE_SENSITIVITY'],check=True)
