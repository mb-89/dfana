import logging
from pyqtgraph.Qt import QtCore, QtGui, QtWidgets
import sys
from functools import partial

def getLogger():return logging.getLogger()

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
