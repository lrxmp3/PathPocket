from pathlib import Path
import os,sys,argparse
p=argparse.ArgumentParser();p.add_argument('run',type=Path);a=p.parse_args()
root=Path(__file__).resolve().parents[1];sys.path.insert(0,str(root/'gui'))
os.environ.setdefault('PATHPOCKET_FRONTEND_BUNDLE',str(root))
os.environ.setdefault('PATHPOCKET_LAUNCHER','REPLAY_NO_SCIENTIFIC_BACKEND')
from PySide6.QtWidgets import QApplication
from pathpocket_gui.ux_app import Window
Window.discover=lambda self:None
def replay_only(self,*args,**kwargs):
    self.fail('This launcher only browses saved results. Use the installed scientific application for a new run.')
Window.call=replay_only
app=QApplication([]);w=Window();w.timer.stop()
w.load_results(str(a.run.resolve()))
presentation=a.run.resolve().parent.parent/'presentation/precomputed'
if (presentation/'thumbnails').is_dir():w.presentation=presentation;w.apply_filter()
w.show();app.exec()
