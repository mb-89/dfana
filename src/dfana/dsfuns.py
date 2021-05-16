from pyqtgraph.Qt import QtCore, QtGui, QtWidgets
from defines import *
import pyqtgraph.dockarea as da
import logging
import pyqtgraph as pg
import sharedWidgets
log = logging.getLogger()

class DataSeriesTree(QtWidgets.QTreeView):
    def __init__(self):
        super().__init__()
        self.mdl = QtGui.QStandardItemModel()
        self.setModel(self.mdl)
        pg.mkQApp().data["dss"] = {}
    def updateMdl(self):
        app = pg.mkQApp()
        self.mdl.clear()
        self.mdl.setColumnCount(2)
        self.setHeaderHidden(True)
        cols = []
        for dfidx,df in app.data["dfs"].items():
            cols.extend(list(df.columns)+[df.index.name])
        colset = set(cols)
        colset.discard(None)
        dss = app.data["dss"]
        for col in sorted(colset):
            for k,v in dss.items():
                if v==col:
                    key=k
                    break
            else:
                key = f"DS{str(len(dss)).zfill(3)}"
                dss[key] = col
            self.mdl.appendRow([
                QtGui.QStandardItem(key),
                QtGui.QStandardItem(col)
                ])


class DataSeriesDock(da.Dock):
    def __init__(self):
        super().__init__("DataSeries", size=(DEFAULT_W/3,DEFAULT_H/5))
        self.setStretch(x=DEFAULT_W/3,y=DEFAULT_H/5)
        self.list = DataSeriesTree()
        self.sel = sharedWidgets.MdlRowSelector(self.list)

        self.addWidget(self.list,row=0,col=0)
        self.addWidget(self.sel,row=1,col=0)