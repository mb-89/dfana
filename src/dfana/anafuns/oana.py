from pyqtgraph.Qt import QtCore, QtGui, QtWidgets
import pyqtgraph as pg
from pyqtgraph import functions as fn

import pandas as pd
import numpy as np
import sharedWidgets
import sys
import os.path as op
import math

sys.path.append(op.dirname(__file__))
import __ana__
from scipy import signal,integrate, interpolate

class Ana(__ana__.Ana):
    name = "oana"
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
        buildplots = self.ana_widget.pw.basequant.count() == 0
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
        if self.showCursors:    self.l.setColumnStretch(1,10)
        else:                   self.l.setColumnStretch(1,0)
        self.meas.setHidden(not self.showCursors)

    def getPlotItem(self):
        return self.pw.getPlotItem()

class SpecPlot(QtWidgets.QWidget):
    redrawSig = QtCore.Signal(bool)

    def __init__(self):
        super().__init__()
        self.basequant = QtWidgets.QComboBox()
        self.osziquant = QtWidgets.QComboBox()

        self.basequant.currentTextChanged.connect(self._redraw)
        self.basequant.setPlaceholderText("<base qantity>")
        self.osziquant.currentTextChanged.connect(self._redraw)
        self.osziquant.setPlaceholderText("<qantity that oscillates at orders of base>")
        self.baseconverter = QtWidgets.QDoubleSpinBox()
        self.baseconverter.setPrefix("conversion factor base -> Hz: ")
        self.baseconverter.setValue(1)
        self.baseconverter.setDecimals(4)
        self.osziconverter = QtWidgets.QDoubleSpinBox()
        self.osziconverter.setPrefix("conversion factor oszi -> Hz: ")
        self.osziconverter.setSuffix(" [ if applicable]")
        self.osziconverter.setValue(1)
        self.osziconverter.setDecimals(4)
        self.osziconverter.valueChanged.connect(self._redraw)
        self.baseconverter.valueChanged.connect(self._redraw)

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
        l1.addWidget(self.basequant)
        l1.addWidget(self.baseconverter)
        l1.addWidget(self.osziquant)
        l1.addWidget(self.osziconverter)
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
            self.basequant.addItem(name)
            self.osziquant.addItem(name)

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

        x0 = self.T[0]
        dx = self.T[-1]-x0
        y0 = 0
        dy = self.f[-1]

        rect = QtCore.QRectF(x0,y0,dx,dy)
        self.img.setRect(rect)
        self.hist.setLevels(np.min(self.Sxx), np.percentile(self.Sxx,97))
        for x in self.pi.axes:
            ax = self.pi.getAxis(x)
            ax.setZValue(1)

    def calc(self, onlyOnChange=False):
        basename = self.basequant.currentText()
        osziname = self.osziquant.currentText()
        basefak = self.baseconverter.value()
        oszifak = self.osziconverter.value()
        try:
            basecol = [x for x in self.datasrc.curves if x.name() == basename][0]
            oszicol = [x for x in self.datasrc.curves if x.name() == osziname][0]
        except IndexError:
            return "no src data specified"
        range=self.range


        T = basecol.xData
        mask = np.logical_and(T>=range[0],T<=range[1])
        T = T[mask]
        newt0t1 = [T[0],T[-1]]
        tchanged = not (newt0t1 == self.t0t1)
        if (not tchanged) and onlyOnChange:return "no change in data"

        self.t0t1 = newt0t1

        basevals = basecol.yData[mask]*basefak
        oszivals = oszicol.yData[mask]*oszifak

        angle = integrate.cumtrapz(basevals, T, initial=0)
        df = pd.DataFrame(data={"y":oszivals,"x":angle},index=angle)
        df.drop_duplicates(inplace=True)
        try: finterp = interpolate.interp1d(df.index, df["y"], kind='cubic')
        except ValueError: return "interpolation failed"
        anglenew = np.linspace(0,angle[-1],len(T))
        ynew = finterp(anglenew)

        Y = ynew
        T = anglenew
        L = len(T)
        self.f, self.t, self.Sxx = signal.spectrogram(
                Y, 
                1/((T[-1]-T[0])/L),
                scaling = 'spectrum',
                mode='magnitude')
        self.Sxx*=2.0
        self.f*= 1.0/(2*math.pi)
        self.T = T

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
