from pyqtgraph.Qt import QtCore, QtGui, QtWidgets
from defines import *
import pyqtgraph.dockarea as da
import pyqtgraph as pg
import logging
import parsers
from functools import partial
log = logging.getLogger()

class DataFrameTree(QtWidgets.QTreeView):
    fileDropped = QtCore.Signal(str)
    def __init__(self):
        super().__init__()
        self.setDragDropMode(QtWidgets.QAbstractItemView.DropOnly)
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
class DataFrameDock(da.Dock):
    def __init__(self):
        super().__init__("DataFrames", size=(DEFAULT_W/3,DEFAULT_H/5))
        self.setStretch(x=DEFAULT_W/3,y=DEFAULT_H/5)
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
        self.moni = QtWidgets.QPushButton("moni")
        #self.moni.setCheckable(True)
        l.addWidget(self.path)
        l.addWidget(self.browse)
        #l.addWidget(self.moni)
        row.setLayout(l)

        self.list = DataFrameTree()
        self.filt = QtWidgets.QLineEdit()
        self.filt.setPlaceholderText("<df filter expr>")
        self.addWidget(row,row=0,col=0)
        self.addWidget(self.list,row=1,col=0)
        self.addWidget(self.filt,row=2,col=0)

        self.openaction = QtGui.QAction(pg.mkQApp())
        self.openaction.setText("parse file(s)")
        self.openaction.setShortcut("CTRL+O")
        self.openaction.triggered.connect(self.browse.click)
        self.addAction(self.openaction)

        self.list.fileDropped.connect(self.append2parseQueue)
        pg.mkQApp().data["dfs"] = {}

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
        self.resultsPending-=1
        if self.resultsPending==0:
            log.info("all parser threads done.")
