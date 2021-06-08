from gui import *
import logfuns
import argparse
from functools import partial

app = pg.mkQApp("dfana")
win = QtGui.QMainWindow()

win.setStatusBar(logfuns.LogBar(win))
win.addDockWidget(QtCore.Qt.BottomDockWidgetArea, logfuns.LogWidget(win))

changeStyle()
area = DockArea()
win.setCentralWidget(area)
win.resize(DEFAULT_W,DEFAULT_H)
area.addWidgets()
win.setWindowTitle('dfana')
win.show()

parser = argparse.ArgumentParser()
parser.add_argument('-read', nargs='+')
args = vars(parser.parse_args())

def parseargs():
    if args["read"]:
        rd = args["read"]
        for idx,p in enumerate(rd):
            f = partial(win.centralWidget().docks["DataFrames"].append2parseQueue, p)
            QtCore.QTimer.singleShot(idx, f)

QtCore.QTimer.singleShot(0, parseargs)
pg.mkQApp().exec()

