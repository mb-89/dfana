from pyqtgraph.Qt import QtCore, QtGui, QtWidgets
import pyqtgraph as pg
from pyqtgraph import functions as fn

import numpy as np
import sharedWidgets
import sys
import os.path as op
sys.path.append(op.dirname(__file__))
import __ana__
from scipy import signal

class Ana(__ana__.Ana):
    name = "spec"
    def ana_show(self, show):
        setHidden = not show
        self.ana_region.setVisible(show)
        super().ana_show(show)

    def ana_getWidget(self):
        if not self.ana_widget:
            plt = SpecContainer(parent=self)
            plt.setHidden(True)
            self.ana_region = sharedWidgets.RelPosLinearRegion(self.ana_parent, self.ana_updateRegion)
            self.ana_widget = plt
            plt.setVisible(False)
            self.ana_widget.setVisible(False)
        return self.ana_widget

    def ana_updateRegion(self,reg):
        if not self.isVisible(): return
        x0x1 = reg.getRegion()
        timeplt = self.ana_parent
        specplt = self.ana_widget.pw
        pi = specplt.pi
        buildplots = self.ana_widget.pw.colsel.count() == 0
        specplt.range=x0x1
        if buildplots: specplt.setData(self.ana_parent)
        specplt.redraw()

    
class SpecContainer(QtWidgets.QWidget):
    def __init__(self,parent):
        super().__init__()
        self.l = QtWidgets.QGridLayout()
        l = self.l
        self.setLayout(l)
        l.setSpacing(0)
        l.setContentsMargins(0,0,0,0)
        self.pw = SpecPlot()
        self.meas = sharedWidgets.ImageMeasWidget(self.pw.pi)
        self.pw.showcursorsfun = lambda s: self.showcursorsfun(s)
        self.range = [0,0]
        l.addWidget(self.pw,0,0)
        l.addWidget(self.meas,0,1)
        l.setColumnStretch(0,39)
        l.setColumnStretch(1,0)
    
    def setVisible(self,vis):
        self.pw.setVisible(vis)
        super().setVisible(vis)

    def showcursorsfun(self, show):
        self.showCursors = show
        if self.showCursors:    self.l.setColumnStretch(1,15)
        else:                   self.l.setColumnStretch(1,0)
        self.meas.setHidden(not self.showCursors)

    def getPlotItem(self):
        return self.pw.getPlotItem()

class SpecPlot(QtWidgets.QWidget):
    winlenbase = 256
    winlenmaxrel = 8
    redrawSig = QtCore.Signal(bool)

    def __init__(self):
        super().__init__()
        self.colsel = QtWidgets.QComboBox()
        self.winlen = QtWidgets.QSpinBox()
        self.winlen.setSingleStep(self.winlenbase)
        self.winlen.setMinimum(self.winlenbase)
        self.winlen.setMaximum(self.winlenbase*self.winlenmaxrel)
        self.winlen.setPrefix("winlen ")
        self.winlen.setSuffix(" samples")
        self.winlen.valueChanged.connect(self._redraw)
        self.colsel.currentTextChanged.connect(self._redraw)
        self.pw = pg.PlotWidget(self)
        self.pw.setSizePolicy(QtWidgets.QSizePolicy.MinimumExpanding,QtWidgets.QSizePolicy.MinimumExpanding)
        self.pi = self.pw.getPlotItem()
        self.img = pg.ImageItem()
        self.img.setOpts(axisOrder='row-major')
        self.pi.addItem(self.img)
        l = QtWidgets.QVBoxLayout()
        self.setLayout(l)
        l.setSpacing(0)
        l.setContentsMargins(0,0,0,0)
        l1 = QtWidgets.QHBoxLayout()
        l1.setSpacing(0)
        l1.setContentsMargins(0,0,0,0)
        l1.addWidget(self.colsel)
        l1.addWidget(self.winlen)
        l.addLayout(l1)
        l.addWidget(self.pw)
        l.addWidget(self.buildHist())

        self.datasrc = None
        self.t0t1 = None
        self.redrawproxy = pg.SignalProxy(self.redrawSig, rateLimit=3, slot=self._redraw)

    def buildHist(self):
        self.histCont = HoriHistContainer()
        self.histCont.setMaximumHeight(75)
        self.hist = self.histCont.hist
        self.hist.setImageItem(self.img)
        return self.histCont

    def setData(self, datasrc):
        self.datasrc = datasrc
        for idx,curve in enumerate(datasrc.curves):
            name = curve.name()
            self.colsel.addItem(name)

    def setVisible(self,vis):
        super().setVisible(vis)
        if vis:self.redraw()

    def redraw(self,_=None):
        if not self.isVisible():return
        self.redrawSig.emit(True)

    def _redraw(self,_=None,onlyOnChange=False):
        calcAborted = self.calc(onlyOnChange)
        if calcAborted:return
        self.img.setImage(self.Sxx)
        self.img.resetTransform()

        x0 = self.t0t1[0]
        dx = self.t0t1[1]-x0
        y0 = 0
        dy = self.fs/2.0

        rect = QtCore.QRectF(x0,y0,dx,dy)
        self.img.setRect(rect)
        self.hist.setLevels(np.min(self.Sxx), np.percentile(self.Sxx,97))
        for x in self.pi.axes:
            ax = self.pi.getAxis(x)
            ax.setZValue(1)
        Y = self.Y/np.max(np.abs(self.Y))*dy
        try:
            self.pltline.setData(self.T,Y)
        except AttributeError:
            pen = fn.mkPen((1,1),style=QtCore.Qt.DotLine)
            self.pltline = self.pw.plot(self.T,Y,pen=pen)
        self.pi.setLimits(yMin=y0, yMax=y0+dy, xMin=y0,xMax=x0+dx)


    def calc(self, onlyOnChange=False):
        colname = self.colsel.currentText()
        col = [x for x in self.datasrc.curves if x.name() == colname][0]
        range=self.range

        Y = col.yData
        T = col.xData
        mask = np.logical_and(T>=range[0],T<=range[1])
        T = T[mask]
        Y = Y[mask]
        L = len(T)
        newt0t1 = [T[0],T[-1]]
        tchanged = not (newt0t1 == self.t0t1)
        self.T = T
        self.Y = Y

        if (not tchanged) and onlyOnChange:return -1
        self.t0t1 = newt0t1
        self.fs = 1.0/((T[-1]-T[0])/len(T))
        windowLen = self.winlen.value()

        self.f, self.t, self.Sxx = signal.spectrogram(
                Y, 
                1/((T[-1]-T[0])/L),
                scaling = 'spectrum',
                mode='magnitude',
                nperseg= windowLen,)
                #noverlap=self.windowOverlap)
        self.Sxx*=2.0
        return 0

class HoriHistContainer(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()
        l = QtWidgets.QHBoxLayout()
        l.setSpacing(0)
        l.setContentsMargins(0,0,0,0)
        self.setLayout(l)
        self.hist=HoriHist()
        gl = pg.GraphicsLayoutWidget()
        gl.addItem(self.hist)
        l.addWidget(gl)

class HoriHist(pg.HistogramLUTItem):
    def __init__(self, image=None, fillHistogram=True, rgbHistogram=False, levelMode='mono'):
        pg.GraphicsWidget.__init__(self)
        self.lut = None
        self.imageItem = lambda: None  # fake a dead weakref
        self.levelMode = levelMode
        self.rgbHistogram = rgbHistogram
        
        self.layout = QtGui.QGraphicsGridLayout()
        self.setLayout(self.layout)
        self.layout.setContentsMargins(1,1,1,1)
        self.layout.setSpacing(0)
        self.vb = pg.ViewBox(parent=self)
        self.vb.setMaximumHeight(20)
        self.vb.setMinimumHeight(20)
        self.vb.setMouseEnabled(x=False, y=True)

        self.gradient = pg.GradientEditorItem()
        self.gradient.setOrientation('top')
        self.gradient.loadPreset('viridis')

        self.gradient.setFlag(self.gradient.ItemStacksBehindParent)
        self.vb.setFlag(self.gradient.ItemStacksBehindParent)
        self.layout.addItem(self.gradient, 0, 0)
        self.layout.addItem(self.vb, 1, 0)
        self.axis = pg.AxisItem('bottom', linkView=self.vb, maxTickLength=-10, parent=self)
        self.layout.addItem(self.axis, 2, 0)

        self.regions = [
            pg.LinearRegionItem([0, 1], 'vertical', swapMode='block'),
            #we dont need those here
            #pg.LinearRegionItem([0, 1], 'vertical', swapMode='block', pen='r',brush=fn.mkBrush((255, 50, 50, 50)), span=(0., 1/3.)),
            #pg.LinearRegionItem([0, 1], 'vertical', swapMode='block', pen='g',brush=fn.mkBrush((50, 255, 50, 50)), span=(1/3., 2/3.)),
            #pg.LinearRegionItem([0, 1], 'vertical', swapMode='block', pen='b',brush=fn.mkBrush((50, 50, 255, 80)), span=(2/3., 1.)),
            #pg.LinearRegionItem([0, 1], 'vertical', swapMode='block', pen='w',brush=fn.mkBrush((255, 255, 255, 50)), span=(2/3., 1.))
            ]
        for region in self.regions:
            region.setZValue(1000)
            self.vb.addItem(region)
            region.lines[0].addMarker('<|', 0.5)
            region.lines[1].addMarker('|>', 0.5)
            region.sigRegionChanged.connect(self.regionChanging)
            region.sigRegionChangeFinished.connect(self.regionChanged)
        self.region = self.regions[0]

        add = QtGui.QPainter.CompositionMode_Plus
        self.plots = [
            pg.PlotCurveItem(pen=(200, 200, 200, 100)),  # mono
            pg.PlotCurveItem(pen=(255, 0, 0, 100), compositionMode=add),  # r
            pg.PlotCurveItem(pen=(0, 255, 0, 100), compositionMode=add),  # g
            pg.PlotCurveItem(pen=(0, 0, 255, 100), compositionMode=add),  # b
            pg.PlotCurveItem(pen=(200, 200, 200, 100), compositionMode=add),  # a
            ]
        self.plot = self.plots[0]
        for plot in self.plots:
            self.vb.addItem(plot)
        self.fillHistogram(fillHistogram)

        self.range = None
        self.gradient.sigGradientChanged.connect(self.gradientChanged)
        self.vb.sigRangeChanged.connect(self.viewRangeChanged)

    def paint(self, p, *args):
        if self.levelMode != 'mono':
            return
        
        pen = self.region.lines[0].pen
        rgn = self.getLevels()
        p1 = self.vb.mapFromViewToItem(self, pg.Point(rgn[0],self.vb.viewRect().center().y()))
        p2 = self.vb.mapFromViewToItem(self, pg.Point(rgn[1],self.vb.viewRect().center().y()))
        gradRect = self.gradient.mapRectToParent(self.gradient.gradRect.rect())
        p.setRenderHint(QtGui.QPainter.Antialiasing)
        for pen in [fn.mkPen((0, 0, 0, 100), width=3), pen]:
            p.setPen(pen)
            p.drawLine(p1 - pg.Point(5, 0), gradRect.bottomLeft())
            p.drawLine(p2 + pg.Point(5, 0), gradRect.bottomRight())
            p.drawLine(gradRect.topLeft(), gradRect.bottomLeft())
            p.drawLine(gradRect.topRight(), gradRect.bottomRight())
