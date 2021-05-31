from pyqtgraph.Qt import QtCore, QtGui, QtWidgets
from defines import *
import pyqtgraph.dockarea as da
import pyqtgraph as pg
import logging
import parsers
from functools import partial
import sharedWidgets
import os.path as op
import itertools
import pandas as pd

log = logging.getLogger()

class DataFrameTree(QtWidgets.QTreeView):
    fileDropped = QtCore.Signal(str)
    updated = QtCore.Signal()
    def __init__(self):
        super().__init__()
        self.setDragDropMode(QtWidgets.QAbstractItemView.DropOnly)
        self.setSelectionMode(QtWidgets.QAbstractItemView.SelectionMode.ExtendedSelection)
        self.mdl = QtGui.QStandardItemModel()
        self.setItemDelegate(sharedWidgets.DelegateWithSelectorMarker())
        self.setModel(self.mdl)

    def dragEnterEvent(self, e):
        if e.mimeData().hasUrls():  e.accept()
        else:                       e.ignore()
    def dragMoveEvent(self, e):
        if e.mimeData().hasUrls():
            e.setDropAction(QtCore.Qt.CopyAction)
            e.accept()
        else:
            e.ignore()
    def dropEvent(self, e):
        if e.mimeData().hasUrls():
            e.accept()
            for url in e.mimeData().urls():
                self.fileDropped.emit(str(url.toLocalFile()))
        else:
            e.ignore()

    def updateMdl(self):
        self.mdl.clear()
        self.mdl.setColumnCount(2)
        self.setHeaderHidden(True)
        for dfidx,df in pg.mkQApp().data["dfs"].items():
            self.mdl.appendRow([
                QtGui.QStandardItem(dfidx),
                QtGui.QStandardItem(df.attrs["name"])
                ])
        self.updated.emit()

class DataFrameDock(da.Dock):
    def __init__(self):
        app = pg.mkQApp()
        app.data["dfs"] = {}

        super().__init__("DataFrames", size=(DEFAULT_W/3,DEFAULT_H/5))
        self.setStretch(x=DEFAULT_W/5*2,y=DEFAULT_H/5)
        self.parsequeue=[]
        self.resultsPending = 0
        self.parsing = False
        row = QtWidgets.QWidget()
        l = QtWidgets.QHBoxLayout()
        l.setSpacing(0)
        l.setContentsMargins(0,0,0,0)
        self.path = QtWidgets.QComboBox()
        self.path.setEditable(True)
        self.path.setPlaceholderText("<path or glob expr + return>")
        self.browse = QtWidgets.QPushButton("browse")
        self.browse.setSizePolicy(QtWidgets.QSizePolicy.Minimum,QtWidgets.QSizePolicy.Minimum)
        self.browse.setMinimumWidth(75)
        self.browse.setMaximumWidth(100)
        self.browse.clicked.connect(self.getpath)
        self.path.lineEdit().returnPressed.connect(self.append2parseQueue)
        #self.moni = QtWidgets.QPushButton("moni")
        #self.moni.setCheckable(True)
        l.addWidget(self.path)
        l.addWidget(self.browse)
        #l.addWidget(self.moni)
        row.setLayout(l)

        self.list = DataFrameTree()
        self.sel = sharedWidgets.MdlRowSelector(self.list)

        #w = QtWidgets.QWidget()
        #l2 = QtWidgets.QVBoxLayout()
        #l2.setSpacing(0)
        #l2.setContentsMargins(0,0,0,0)
        #w.setLayout(l2)
        #l2.addWidget(row)
        #l2.addWidget(self.list)
        #l2.addWidget(self.sel)
        #self.addWidget(w)

        self.addWidget(row,row=0,col=0)
        self.addWidget(self.list,row=1,col=0)
        self.addWidget(self.sel,row=2,col=0)
        self.topLayout.setRowStretch(0,1)
        self.topLayout.setRowStretch(1,100)
        self.topLayout.setRowStretch(2,1)

        self.openaction = QtGui.QAction(app)
        self.openaction.setText("parse file(s)")
        self.openaction.setShortcut("CTRL+O")
        self.openaction.triggered.connect(self.browse.click)
        self.addAction(self.openaction)
        self.list.fileDropped.connect(self.append2parseQueue)

    def getpath(self):
        files = QtWidgets.QFileDialog.getOpenFileName()
        files = files[0]
        if not files:return
        path=files.replace("\\","/")
        self.path.lineEdit().setText(path)
        self.append2parseQueue()

    def append2parseQueue(self, path = None):
        if path is None:
            path = self.path.lineEdit().text()
            self.path.lineEdit().clear()
        self.parsequeue.append(path)
        self.parsenext()

    def parsenext(self):
        if self.parsing: return
        if not self.parsequeue: return
        self.parsing=True
        path = self.parsequeue.pop(0)
        if path: self._parse(path)
        self.parsing=False
        if self.parsequeue:QtCore.QTimer.singleShot(0, self.parsenext)

    def _parse(self, path):
        log.info(f"parsing {path}...")
        for qr in parsers.prepare(path):
            qr.signaller.done.connect(self._acceptResult)
            self.resultsPending+=1
            log.info(f"started collecting dataframes from {qr.path}...")
            if MULTITHREAD: QtCore.QThreadPool.globalInstance().start(qr)
            else:
                f = partial(qr.run)
                QtCore.QTimer.singleShot(0,f)
        if not self.resultsPending:
            log.warning("path not accepted by any installed parser.")
        
    def _acceptResult(self, result):
        path = result["path"]
        result = result["result"]
        log.info(f"done collecting dataframes from {path}, found {len(result)} dfs")
        for df in result:
            pg.mkQApp().data["dfs"][df.attrs["_idx"]]=df
        self.resultsPending-=1
        self.list.updateMdl()
        if self.resultsPending==0:
            log.info("all parser threads done.")

def getMetaDataoverview(dfs):
    if isinstance(dfs, dict):dfs = dfs.values()
    if len(dfs)<=1: return None
    allMetaData = [x.attrs for x in dfs]
    names = [x["name"] for x in allMetaData]
    commonprefix = op.commonprefix(names)
    names = [x.replace(commonprefix,"") for x in names]
    allMetaData = [x.attrs for x in dfs]
    allAttrs = sorted(list(set(itertools.chain(*(tuple(x.keys()) for x in allMetaData)))))

    header = {"nameprefix": commonprefix} if commonprefix else {"nameprefix":"no name commonalities"}
    for k in allAttrs:
        attrcollection = [x.get(k) for x in allMetaData]
        attrcollection = [x for x in attrcollection if x is not None]
        if len(set(attrcollection))==1:
            header[k] = attrcollection[0]

    rows = []
    for name, md in zip(names, allMetaData):
        dfdict = {}
        for k in [x for x in allAttrs if x not in header]:
            if k == "name":continue
            dfdict[k] = md.get(k)
        
        if commonprefix:    dfdict[f"name [{commonprefix}...]"] = "..."+name
        else:               dfdict["name"] = name
        rows.append(dfdict)

    df = pd.DataFrame(rows)
    df.set_index("_idx",inplace=True)
    df.sort_index(inplace=True)
    df.attrs = header
    return df

def getDataOverview(dfs):
    if isinstance(dfs, dict):dfs = dfs.values()
    allCols = [x.columns for x in dfs]
    header = sorted(list(set(itertools.chain(*allCols))))
    rows = []
    for df in dfs:
        row = {}
        row["_idx"] = df.attrs["_idx"]
        row["dfname"] = df.attrs["name"]
        row |= dict((x,("" if x not in df else "X")) for x in header)
        rows.append(row)

    df = pd.DataFrame(rows)
    df.set_index("_idx",inplace=True)
    df.sort_index(inplace=True)
    #df.attrs = header
    return df