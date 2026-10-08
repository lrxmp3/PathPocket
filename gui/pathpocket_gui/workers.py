from PySide6.QtCore import QObject,QRunnable,Signal,QThreadPool
class Signals(QObject):
    done=Signal(object);error=Signal(str)
class Work(QRunnable):
    def __init__(self,fn):
        super().__init__();self.setAutoDelete(False);self.fn=fn;self.signals=Signals()
    def run(self):
        try:self.signals.done.emit(self.fn())
        except Exception as e:self.signals.error.emit(str(e))
def background(fn,done,error):
    w=Work(fn);w.signals.done.connect(done);w.signals.error.connect(error);QThreadPool.globalInstance().start(w);return w
