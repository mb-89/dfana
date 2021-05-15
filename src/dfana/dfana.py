import PySide6
import pyqtgraph as pg
from pyqtgraph.Qt import QtCore, QtGui, QtWidgets
import pyqtgraph.dockarea as da
import logging
import sys
from functools import partial
import os.path as op
import parsers

log = logging.getLogger()

DEFAULT_H = 500
DEFAULT_W = 1000

class StreamToLogger():
    """
    Fake file-like stream object that redirects writes to a logger instance.
    https://www.electricmonk.nl/log/2011/08/14/redirect-stdout-and-stderr-to-a-logger-in-python/
    """
    def __init__(self, logger, log_level=logging.INFO):
        self.logger = logger
        self.log_level = log_level
        self.linebuf = ''

    def write(self, buf):
        for line in buf.rstrip().splitlines():
            self.logger.log(self.log_level, line.rstrip())
    def flush(self):pass
class LogBar(QtWidgets.QStatusBar):
    log2bar = QtCore.Signal(str)
    def __init__(self, parent):
        super().__init__(parent)
        self.setup()
    def setup(self):
        log = logging.getLogger()

        log.setLevel(logging.DEBUG)
        formatter = logging.Formatter('%(relativeCreated)08d %(levelname)s: %(message)s')
        log._fmt = formatter

        logging.addLevelName(logging.DEBUG, 'DBG ')
        logging.addLevelName(logging.INFO, 'INFO')
        logging.addLevelName(logging.WARNING, 'WARN')
        logging.addLevelName(logging.ERROR, 'ERR ')

        #reroute stdin, stderr
        log._STDerrLogger = StreamToLogger(log, logging.ERROR)
        log._origSTDerr = sys.stderr
        sys.stderr = log._STDerrLogger
        log._STDoutLogger = StreamToLogger(log, logging.INFO)
        log._origSTDout = sys.stdout
        sys.stdout = log._STDoutLogger

        #add to console
        ch = logging.StreamHandler(log._origSTDout)
        ch.setLevel(logging.DEBUG)
        ch.setFormatter(log._fmt)
        log.addHandler(ch)

        #add to statusbar
        fn = lambda x: self.showMessage(x, 0)
        connectLog2fn(log, fn, self.log2bar)
def connectLog2fn(log, fn ,s):
    #emit function to connect log msgs to qt signals:
    def emit(obj, sig, logRecord):
        msg = obj.format(logRecord)
        sig.emit(msg)

    hdl = logging.StreamHandler()
    hdl.setFormatter(log._fmt)
    hdl.setLevel(logging.DEBUG)
    hdl.emit = partial(emit,hdl,s)
    s.connect(fn)
    log.addHandler(hdl)
class LogWidget(QtWidgets.QDockWidget):
    log2wid = QtCore.Signal(str)
    def __init__(self, window):
        super().__init__()
        self.lw = QtWidgets.QPlainTextEdit()
        self.setTitleBarWidget(QtWidgets.QWidget()) 
        f = QtGui.QFont("monospace")
        f.setStyleHint(QtGui.QFont.TypeWriter)
        self.lw.setFont(f)
        self.lw.setReadOnly(True)
        self.lw.setUndoRedoEnabled(False)
        self.lw.setTextInteractionFlags(QtCore.Qt.TextSelectableByMouse | QtCore.Qt.TextSelectableByKeyboard)
        self.hide()
        self.setWidget(self.lw)
        self.resize(600,400)
        self.setWindowTitle('log')
        self.append = self.lw.appendPlainText

        log = logging.getLogger()
        connectLog2fn(log, self.append, self.log2wid)
        self.action = QtGui.QAction()
        self.action.setText("toggle log")
        self.action.setShortcut("CTRL+L")
        self.action.triggered.connect(self.togglehide)
        window.addAction(self.action)

    def togglehide(self):
        self.setVisible(self.isHidden())

class DockArea(da.DockArea):
    def __init__(self):
        super().__init__()
        self.nrOfPlots = 0
        pg.mkQApp().data = {}

    def addWidgets(self):
        d1 = DataFrameDock()
        d2 = DataSeriesDock()
        d3 = PlotDock()

        self.addDock(d1)
        self.addDock(d2, "right", d1)
        self.addDock(d3, "right", d2)
        d3.pltsig.connect(self.addPlot)

    def addPlot(self):
        plt = da.Dock(f"Plot #{self.nrOfPlots}", closable=True)
        plt.label.closeButton.setToolButtonStyle(QtCore.Qt.ToolButtonTextOnly)
        plt.label.closeButton.setText("X")
        plt.setStretch(x=DEFAULT_W,y=DEFAULT_H/5*4)
        self.nrOfPlots+=1
        existingPlots = sorted([k for k in self.docks.keys() if k.startswith("Plot #")])
        noTargetFound = False
        offset = 0
        while True:
            offset+=1
            try:
                target =self.docks[existingPlots[-offset]]
                if target.area != self: continue #we dont dock onto floating plots
                self.addDock(plt, "above",target , size=(DEFAULT_W,DEFAULT_H/5*4))
                break
            except TypeError:
                continue
            except (KeyError, IndexError) as e:
                noTargetFound=True
                break
        if noTargetFound: self.addDock(plt, "bottom", size=(DEFAULT_W,DEFAULT_H/5*4))
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
            QtCore.QThreadPool.globalInstance().start(qr)
        if not self.resultsPending:
            log.warning("path not accepted by any installed parser.")
        
    def _acceptResult(self, result):
        path = result["path"]
        result = result["result"]
        log.info(f"done collecting dataframes from {path}, found {len(result)} dfs")
        self.resultsPending-=1
        if self.resultsPending==0:
            log.info("all parser threads done.")

class DataSeriesDock(da.Dock):
    def __init__(self):
        super().__init__("DataSeries", size=(DEFAULT_W/3,DEFAULT_H/5))
        self.setStretch(x=DEFAULT_W/3,y=DEFAULT_H/5)
        self.list = QtWidgets.QTreeView()
        self.filt = QtWidgets.QLineEdit()
        self.filt.setPlaceholderText("<ds filter expr>")
        self.addWidget(self.list,row=0,col=0)
        self.addWidget(self.filt,row=1,col=0)
class PlotDock(da.Dock):
    pltsig = QtCore.Signal()
    def __init__(self):
        super().__init__("Plot options", size=(DEFAULT_W/3,DEFAULT_H/5))
        self.setStretch(x=DEFAULT_W/3,y=DEFAULT_H/5)
        w = QtWidgets.QWidget()
        l = QtWidgets.QVBoxLayout()
        l.setContentsMargins(0,0,0,0)
        l.setSpacing(0)
        l.addSpacerItem(QtWidgets.QSpacerItem(0,0,QtWidgets.QSizePolicy.Maximum,QtWidgets.QSizePolicy.Expanding))

        w.setLayout(l)
        self.addWidget(w)

        self.plt = QtWidgets.QPushButton("plot")
        self.meta = QtWidgets.QPushButton("metadata")
        l.addWidget(self.meta)
        l.addWidget(self.plt)
        self.plt.clicked.connect(self.pltsig.emit)