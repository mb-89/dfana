import pyqtgraph.dockarea as da
import pyqtgraph as pg
import logging
import helperfuns
import math
from functools import partial
from pyqtgraph.Qt import QtCore, QtGui, QtWidgets
import numpy as np

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
        if len(axes[0])>1:axes[0]=axes[0][0]#we store the x axis in axes[0]. we cant have more than 1, and by default we plot against the dataframe index
        X = axes[0]
        Y=[y for y in axes[1:] if y]
        
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
                if x is None: xdata = {"idx":df.index.values}
                else:
                    try: xdata = {x: df[x]}
                    except: continue #if we dont find the x-data, we skip this dataframe
                #collect y data
                ydata = {}
                for trc in traces:
                    try:
                        yd = df[trc].values
                        name = f"{trc} [{df.attrs['_idx']}]"
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
            if xlink is None:xlink=plt.pw
            splitter.addWidget(plt)
        self.addWidget(splitter,row=idx,col=0)

    def buildplot(self, xd,yd,xlink):
        pw = XYplot()
        plt = pw.getPlotItem()
        plt.setDownsampling(auto=True,mode="peak")
        plt.setClipToView(True)
        xname = list(xd.keys())[0]
        plt.addLegend()
        plt.showGrid(1,1,0.75)
        plt.setLabel("left", xname)
        xdata = xd[xname]
        l = len(yd)
        for idx,(yname, ydata) in enumerate(yd.items()):
            try:
                plt.plot(x=xdata,y=ydata,pen=(idx,l), name=yname)
            except:
                log.error(f"could not plot column {name}")
                continue
        if xlink is not None:
            plt.setXLink(xlink)
        return pw

class XYplot(QtWidgets.QWidget):

    def __init__(self):
        super().__init__()
        self.pw = pg.PlotWidget()
        self.pi = self.pw.getPlotItem()

        self.c1 = RelPosCursor(1/3)
        self.c2 = RelPosCursor(2/3)
        self.pi.addItem(self.c1)
        self.pi.addItem(self.c2)
        self.meas = MeasWidget(self.pi,[self.c1,self.c2])

        l = QtWidgets.QGridLayout()
        self.setLayout(l)
        l.setSpacing(0)
        l.setContentsMargins(0,0,0,0)
        l.addLayout(self.createButtons(),0,0)
        l.addWidget(self.pw,0,1)
        l.addWidget(self.meas,0,2)
        l.setColumnStretch(0,1)
        l.setColumnStretch(1,20)
        l.setColumnStretch(2,0)
        self.l = l

    def createButtons(self):
        buttons = QtWidgets.QVBoxLayout()
        buttons.setSpacing(0)
        buttons.setContentsMargins(0,0,0,0)

        closebutton = QtWidgets.QPushButton("X")
        buttons.addWidget(closebutton)
        closebutton.clicked.connect(self.close)

        cursbutton = QtWidgets.QPushButton("cursor")
        buttons.addWidget(cursbutton)
        cursbutton.clicked.connect(self.togglecursors)
        return buttons

    def togglecursors(self):
        if self.meas.isHidden():    self.l.setColumnStretch(2,2)
        else:                       self.l.setColumnStretch(2,0)
        self.meas.toggle()
        
        self.c1.toggle()
        self.c2.toggle()

    def getPlotItem(self):
        return self.pw.getPlotItem()
    def toggle(self):
        self.setHidden(not self.isHidden())

class RelPosCursor(pg.InfiniteLine):
    def __init__(self, startposrel):
        super().__init__(angle=90,movable=True)
        self.setVisible(False)
        self.startposrel = startposrel
        self.currposrel = startposrel
    def toggle(self):
        willbevisible = not self.isVisible()
        if willbevisible:
            self.setRelPos(self.startposrel)
        self.setVisible(willbevisible)
    def setPos(self,pos):
        try:
            x0,x1 = self.getViewBox().viewRange()[0]
            dx = x1-x0
            self.currposrel = (pos-x0)/dx
        except AttributeError:
            pass

        super().setPos(pos)

    def setRelPos(self, relpos=None):
        if relpos is None: relpos = self.currposrel
        x0,x1 = self.getViewBox().viewRange()[0]
        dx = x1-x0
        self.setValue(x0+relpos*dx)

    def viewTransformChanged(self):
        self.setRelPos()
        return super().viewTransformChanged()

class MeasWidget(QtWidgets.QLabel):
    def __init__(self, plt, cursors):
        super().__init__("")
        self.plt = plt
        self.cursors=dict((idx,c) for idx,c in enumerate(cursors))
        self.setHidden(True)
        self.proxies = [pg.SignalProxy(c.sigPositionChanged, rateLimit=30, slot=self.updateVals) for c in cursors]
        self.values = [tuple() for x in self.cursors]
        for k,v in self.cursors.items():
            v.idx = k

    def toggle(self):
        self.setHidden(not self.isHidden())
    def updateVals(self,c):
        if self.isHidden():return
        c = c[-1]
        xval = c.pos()[0]
        yvals = tuple(curve.yData[np.searchsorted(curve.xData, xval, side="left")] for curve in self.plt.curves)
        self.values[c.idx] = (xval,*yvals)
        self.updateText()
    def updateText(self):
        lines = []
        for idx,v in enumerate(self.values):
            lines.append(f"{idx}: {v}")
        self.setText("\n".join(lines))
