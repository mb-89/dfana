import PySide6
import pyqtgraph as pg
from pyqtgraph.Qt import QtCore, QtGui, QtWidgets
import pyqtgraph.dockarea as da
from qt_material import apply_stylesheet
from functools import partial

import os.path as op
import logging
import dffuns
import dsfuns
import pltfuns
import exportfuns
import sharedWidgets
import gc
from defines import *
import os
import os.path as op

log = logging.getLogger()
ONEDFPERPLOT = False

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
        d3.exportsig.connect(self.exportPlot)

    def addPlot(self):
        app = pg.mkQApp()
        dfs = self.docks["DataFrames"].sel.getSelectedIdxs()
        if not dfs: dfs = dict((x, set([0])) for x in app.data["dfs"].keys())
        dfs = tuple(dfs.keys())
        dss = self.docks["DataSeries"].sel.getSelectedIdxs()

        if ONEDFPERPLOT:
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

                cl = partial(self.cleanup, plt._name)
            plt.sigClosed.connect(cl)
        else:
            plt = pltfuns.PltDock(self.nrOfPlots,dfs,dss,app.data)
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

            cl = partial(self.cleanup, plt._name)
            plt.sigClosed.connect(cl)

    def exportPlot(self):
        plts = tuple((k,v) for k,v in self.docks.items() if k.startswith("Plot #"))
        if not plts:return
        for plt in plts:
            if not plt[1].visibleRegion().isEmpty():
                exportfuns.export(plt[0],plt[1])

    def cleanup(self, dockname, extraArg):
        dck = self.docks.pop(dockname)
        dck.deleteLater()
        del dck
        gc.collect()

class ActionsDock(da.Dock):
    pltsig = QtCore.Signal()
    exportsig = QtCore.Signal()
    def __init__(self):
        super().__init__("Actions", size=(DEFAULT_W/3,DEFAULT_H/5))
        self.setStretch(x=DEFAULT_W/5,y=DEFAULT_H/5)
        w = QtWidgets.QWidget()
        l = QtWidgets.QVBoxLayout()
        l.setContentsMargins(0,0,0,0)
        l.setSpacing(0)
        l.addSpacerItem(QtWidgets.QSpacerItem(0,0,QtWidgets.QSizePolicy.Maximum,QtWidgets.QSizePolicy.Expanding))

        w.setLayout(l)
        self.addWidget(w)

        self.plt = QtWidgets.QPushButton("plot")
        self.meta = QtWidgets.QPushButton("meta")
        self.dataOverview = QtWidgets.QPushButton("data overview")
        self.srcbut = QtWidgets.QPushButton("open dfana src")
        self.xbut = QtWidgets.QPushButton("Export")

        l.addWidget(self.srcbut)
        l.addWidget(self.dataOverview)
        l.addWidget(self.meta)
        l.addWidget(self.xbut)
        l.addWidget(self.plt)

        self.srcbut.clicked.connect(lambda: os.startfile(op.dirname(__file__)))
        self.meta.clicked.connect(self.showMetaData)
        self.dataOverview.clicked.connect(self.showDataOverview)
        self.plt.clicked.connect(self.pltsig.emit)
        self.xbut.clicked.connect(self.exportsig.emit)
        self.metaView = None

    def showMetaData(self):
        if self.metaView:
            self.metaView.close()
        app = pg.mkQApp()
        dfs = app.data["dfs"]
        if not dfs:return
        dfmeta = dffuns.getMetaDataoverview(dfs)
        self.metaView = sharedWidgets.DFview(dfmeta)
        self.metaView.setWindowTitle("Dataframe metadata overview")
        self.metaView.show()

    def showDataOverview(self):
        if self.metaView:
            self.metaView.close()
        app = pg.mkQApp()
        dfs = app.data["dfs"]
        if not dfs:return
        dfmeta = dffuns.getDataOverview(dfs)
        self.metaView = sharedWidgets.DFview(dfmeta)
        self.metaView.setWindowTitle("Dataframe content overview")
        self.metaView.show()