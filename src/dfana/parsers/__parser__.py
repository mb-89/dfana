from PySide6 import QtCore
import time
from pandas import DataFrame

#https://stackoverflow.com/a/62027329
class Signaller(QtCore.QObject):
    done = QtCore.Signal(dict)

class Parser(QtCore.QRunnable):
    def __init__(self,path,tempdir=None):
        super().__init__()
        self._signaller = Signaller()
        self.path = path
        self.accepted = self.accept()
        self.consumedPaths = self.consumePaths()
        self.tempdir = tempdir

    @property
    def signaller(self):
        return self._signaller

    def accept(self):
        return False
    def consumePaths(self):
         return [self.path]

    def run(self):
        time.sleep(1)
        self.signaller.done.emit({"path":self.path, "result": self.path})