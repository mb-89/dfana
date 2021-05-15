import dfana
import logfuns
from qt_material import apply_stylesheet
import argparse
from functools import partial

app = dfana.pg.mkQApp("dfana")
win = dfana.QtGui.QMainWindow()

win.setStatusBar(logfuns.LogBar(win))
win.addDockWidget(dfana.QtCore.Qt.BottomDockWidgetArea, logfuns.LogWidget(win))

apply_stylesheet(app, theme='dark_amber.xml')
area = dfana.DockArea()
win.setCentralWidget(area)
win.resize(dfana.DEFAULT_W,dfana.DEFAULT_H)
area.addWidgets()
win.setWindowTitle('dfana')
win.show()

parser = argparse.ArgumentParser()
parser.add_argument('-read', nargs='+')
args = vars(parser.parse_args())

if args["read"]:
    rd = args["read"]
    for idx,p in enumerate(rd):
        f = partial(win.centralWidget().docks["DataFrames"].append2parseQueue, p)
        dfana.QtCore.QTimer.singleShot(idx, f)

dfana.pg.mkQApp().exec()

