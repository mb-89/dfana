from PySide6 import QtCore
import time
from pandas import DataFrame

#https://stackoverflow.com/a/62027329
class Signaller(QtCore.QObject):
    done = QtCore.Signal(dict)

dfcnt = 0

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

    def parse_raw(self):
        time.sleep(1)
        return []

    def postprocess(self, dfs):
        global dfcnt
        for df in dfs:
            df.attrs["_idx"] = f"DF{str(dfcnt).zfill(3)}"
            dfcnt+=1
        return dfs

    def run(self):
        dfs_raw = self.parse_raw()
        dfs = self.postprocess(dfs_raw)
        self.signaller.done.emit({"path":self.path, "result": dfs})