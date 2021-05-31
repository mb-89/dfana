import pyqtgraph.dockarea as da
import pyqtgraph as pg
import logging
import helperfuns
import anafuns
import math
from functools import partial
from pyqtgraph.Qt import QtCore, QtGui, QtWidgets
import numpy as np
import sharedWidgets

log = logging.getLogger()

class PltDock(da.Dock):
    def __init__(self,nr,dfsel,dssel,rawdata):
        name = f"Plot #{nr}"
        super().__init__(name, closable=True)
        self.dfsel = dfsel
        self.dssel = dssel
        self.rawdata = rawdata
        self._name = name

        dfs = tuple(x for x in rawdata["dfs"].values() if not dfsel or x.attrs["_idx"] in dfsel)

        #if dssel is empty, we try to create a reasonable overview over the measurements
        #we will improve this later #TODO
        if not dssel:dssel = self.createDataOverview()

        axes = self.groupByTargetAxis(dssel)
        if len(axes[0])>1:axes[0]=[axes[0][0]]#we store the x axis in axes[0]. we cant have more than 1, and by default we plot against the dataframe index
        X = axes[0]
        Y=[y for y in axes[1:] if y]
        if not Y:return
        
        subplts = self.buildPltData(dfs,X,Y)
        self.buildplots(subplts)

    def buildPltData(self, dfs,x,Y):
        subplts = []
        if x: x = self.rawdata["dss"][x[0]]
        else: x = None
        for subplot in Y:
            traces = tuple(self.rawdata["dss"][y] for y in subplot)
            for df in dfs:
                #collect x data
                try: xdata = {x: df[x]}
                except: xdata = {"idx":df.index.values}
                #collect y data
                ydata = {}
                for idx,trc in enumerate(traces):
                    try:
                        yd = df[trc].values
                        name = f"[Y{idx}] {trc} [{df.attrs['_idx']}]"
                        ydata[name]=yd
                    except:continue
            subplts.append((xdata,ydata))
        return subplts

    def createDataOverview(self):
        dct = {}
        LC = math.ceil(len(self.rawdata["dss"])/9)
        chunks = helperfuns.chunks(tuple((k,v) for k,v in self.rawdata["dss"].items()),LC)
        for idx,ch in enumerate(chunks):
            for elem in ch:
                curr = dct.setdefault(elem[0],set())
                curr.add(idx+1)
        return dct

    def groupByTargetAxis(self,dssel):
        axes = []
        for axidx in range(10):
            tmp = []
            for dfidx,axsel in dssel.items():
                if axidx in axsel:
                    tmp.append(dfidx)
            axes.append(tmp)
        return axes

    def buildplots(self, pltdata):
        xlink = None
        splitter = QtWidgets.QSplitter(QtCore.Qt.Vertical)
        for idx,(xd,yd) in enumerate(pltdata):
            if not yd:continue
            plt = self.buildplot(xd,yd,xlink)
            if xlink is None:xlink=plt.pw.pw
            splitter.addWidget(plt)
        self.addWidget(splitter,row=idx,col=0)

    def buildplot(self, xd,yd,xlink):
        pw = PlotDockSubplot()
        plt = pw.pw.pi
        plt.setDownsampling(auto=True,mode="peak")
        plt.setClipToView(True)
        xname = list(xd.keys())[0]
        plt.addLegend()
        plt.showGrid(1,1,0.75)
        plt.setLabel("bottom", xname)
        xdata = xd[xname]
        l = len(yd)
        for idx,(yname, ydata) in enumerate(yd.items()):
            try:
                plt.plot(x=xdata,y=ydata,pen=(idx,l), name=yname)
            except:
                log.error(f"could not plot column {yname}")
                continue
        if xlink is not None:
            plt.setXLink(xlink)
        return pw

class PlotDockSubplot(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()
        self.pw = sharedWidgets.PlotWithMeasWidget()
        l = QtWidgets.QGridLayout()
        spl = QtWidgets.QSplitter(QtCore.Qt.Vertical)
        spl.addWidget(self.pw)
        self.setLayout(l)
        l.setSpacing(0)
        l.setContentsMargins(0,0,0,0)
        buttons, anawidgets = self.createWidgets()
        l.addLayout(buttons,0,0)
        l.addWidget(spl,0,1)
        for idx, plt in enumerate(anawidgets):
            spl.addWidget(plt)
        l.setColumnStretch(0,1)
        l.setColumnStretch(1,20)
        self.l = l

    def createWidgets(self):
        buttons = QtWidgets.QVBoxLayout()
        buttons.setSpacing(0)
        buttons.setContentsMargins(0,0,0,0)

        closebutton = QtWidgets.QPushButton("close")
        buttons.addWidget(closebutton)
        closebutton.clicked.connect(self.close)

        cursbutton = QtWidgets.QPushButton("cursor")
        cursbutton.setCheckable(True)
        buttons.addWidget(cursbutton)
        cursbutton.clicked.connect(self.pw.showcursorsfun)
        self.cursbutton = cursbutton

        anawidgets = []
        for k,fn in anafuns.getFuns().items():
            but = fn(self.pw.pi)
            buttons.addWidget(but)
            anawidgets.append(but.ana_getWidget())
            cursbutton.clicked.connect(but.ana_showMeas)

        return buttons, anawidgets

    def toggle(self):
        self.setHidden(not self.isHidden())