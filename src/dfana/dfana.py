import PySide6
import pyqtgraph as pg
from pyqtgraph.Qt import QtCore, QtGui, QtWidgets
import pyqtgraph.dockarea as da

DEFAULT_H = 500
DEFAULT_W = 1000

class DockArea(da.DockArea):
    def __init__(self):
        super().__init__()
        self.nrOfPlots = 0
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


class DataFrameDock(da.Dock):
    def __init__(self):
        super().__init__("DataFrames", size=(DEFAULT_W/3,DEFAULT_H/5))
        self.setStretch(x=DEFAULT_W/3,y=DEFAULT_H/5)
        self.list = QtWidgets.QTreeView()
        self.filt = QtWidgets.QLineEdit()
        self.addWidget(self.list,row=0,col=0)
        self.addWidget(QtWidgets.QLabel("df filters"),row=1,col=0)
        self.addWidget(self.filt,row=2,col=0)

class DataSeriesDock(da.Dock):
    def __init__(self):
        super().__init__("DataSeries", size=(DEFAULT_W/3,DEFAULT_H/5))
        self.setStretch(x=DEFAULT_W/3,y=DEFAULT_H/5)
        self.list = QtWidgets.QTreeView()
        self.filt = QtWidgets.QLineEdit()
        self.addWidget(self.list,row=0,col=0)
        self.addWidget(QtWidgets.QLabel("ds filters"),row=1,col=0)
        self.addWidget(self.filt,row=2,col=0)

class PlotDock(da.Dock):
    pltsig = QtCore.Signal()
    def __init__(self):
        super().__init__("Plot options", size=(DEFAULT_W/3,DEFAULT_H/5))
        self.setStretch(x=DEFAULT_W/3,y=DEFAULT_H/5)
        self.plt = QtWidgets.QPushButton("build plot")
        self.addWidget(self.plt,row=0,col=0)
        self.plt.clicked.connect(self.pltsig.emit)
