import PySide6
import pyqtgraph as pg
from pyqtgraph.Qt import QtCore, QtGui, QtWidgets
import pyqtgraph.dockarea as da

import os.path as op
import logging
import dffuns
import dsfuns
from defines import *

log = logging.getLogger()

class DockArea(da.DockArea):
    def __init__(self):
        super().__init__()
        self.nrOfPlots = 0
        pg.mkQApp().data = {}

    def addWidgets(self):
        d1 = dffuns.DataFrameDock()
        d2 = dsfuns.DataSeriesDock()
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