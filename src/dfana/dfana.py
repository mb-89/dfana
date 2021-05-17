import PySide6
import pyqtgraph as pg
from pyqtgraph.Qt import QtCore, QtGui, QtWidgets
import pyqtgraph.dockarea as da
from qt_material import apply_stylesheet

import os.path as op
import logging
import dffuns
import dsfuns
import pltfuns
import sharedWidgets
from defines import *

log = logging.getLogger()

def changeStyle():
    app = pg.mkQApp()
    extra = {}
    apply_stylesheet(app, theme='dark_amber.xml', extra=extra)
    p = app.palette()
    p.setColor(QtGui.QPalette.Text, QtCore.Qt.red)
    app.setPalette(p)

class DockArea(da.DockArea):
    def __init__(self):
        super().__init__()
        self.nrOfPlots = 0
        pg.mkQApp().data = {}
        

    def addWidgets(self):
        d1 = dffuns.DataFrameDock()
        d2 = dsfuns.DataSeriesDock()
        d3 = ActionsDock()

        self.addDock(d1)
        self.addDock(d2, "right", d1)
        self.addDock(d3, "right", d2)
        
        d1.list.updated.connect(d2.list.updateMdl)
        d3.pltsig.connect(self.addPlot)

    def addPlot(self):
        app = pg.mkQApp()
        dfs = self.docks["DataFrames"].sel.getSelectedIdxs()
        if not dfs: dfs = dict((x, set([0])) for x in app.data["dfs"].keys())
        dfs = tuple(dfs.keys())
        dss = self.docks["DataSeries"].sel.getSelectedIdxs()

        #for now, we plot one plot per df. may change later
        for df in dfs:
            singledf = tuple([df])
            plt = pltfuns.PltDock(self.nrOfPlots,singledf,dss,app.data)
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

class ActionsDock(da.Dock):
    pltsig = QtCore.Signal()
    def __init__(self):
        super().__init__("Actions", size=(DEFAULT_W/3,DEFAULT_H/5))
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
        self.meta.clicked.connect(self.showMetaData)
        self.plt.clicked.connect(self.pltsig.emit)
        self.metaView = None

    def showMetaData(self):
        if self.metaView:
            self.metaView.close()
        app = pg.mkQApp()
        dfs = app.data["dfs"]
        if not dfs:return
        dfmeta = dffuns.getDFoverview(dfs)
        self.metaView = sharedWidgets.DFview(dfmeta)
        self.metaView.setWindowTitle("Dataframe metadata overview")
        self.metaView.show()