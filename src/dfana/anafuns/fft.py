from pyqtgraph.Qt import QtCore, QtGui, QtWidgets
import pyqtgraph as pg
from scipy import fft, signal

import numpy as np
import sharedWidgets
import sys
import os.path as op
sys.path.append(op.dirname(__file__))
import __ana__

class Ana(__ana__.Ana):
    name = "fft"

    def ana_toggle(self):
        setHidden = not self.ana_pltw.isHidden()
        self.ana_pltw.setHidden(setHidden)

        if not setHidden:
            ((x0,x1),(y0,y1)) = self.ana_parent.viewRange()
            dx = x1-x0
            xstart = x0+dx/3
            xend = x0+2*dx/3
            self.ana_region.setRegion([xstart,xend])
            self.ana_updateRegion(self.ana_region)
        self.ana_region.setVisible(not setHidden)
        #self.ana_measw.toggle()

    def ana_getPlotWidget(self):
        if not self.ana_pltw:
            plt = pg.PlotWidget(parent=self)
            plt.setHidden(True)
            R = pg.LinearRegionItem()
            self.ana_region = R
            R.setVisible(False)
            self.ana_parent.addItem(R)
            R.sigRegionChanged.connect(self.ana_updateRegion)

            self.ana_pltw = plt
        return self.ana_pltw

    def ana_updateRegion(self,reg):
        if not self.isVisible(): return
        x0x1 = reg.getRegion()
        timeplt = self.ana_parent
        freqplt = self.ana_pltw
        freqplt.showGrid(1,1,0.75)
        freqplt.addLegend()
        pi = freqplt.getPlotItem() 
        buildplots = len(pi.curves) == 0

        for idx,curve in enumerate(timeplt.curves):
            x = curve.xData
            y = curve.yData
            name = curve.name()
            mask = np.logical_and(x>=x0x1[0],x<=x0x1[1])
            x = x[mask]
            y = y[mask]
            N = len(x)
            T = (x[-1]-x[0])/N
            yf = 2.0/N * np.abs(fft.fft(y)[0:N//2])
            xf = np.linspace(0.0, 1.0/(2.0*T),N//2)
            if buildplots:freqplt.plot(x=xf[1:],y=yf[1:],pen=curve.opts['pen'])
            else: pi.curves[idx].setData(x=xf[1:],y=yf[1:])


    def ana_getMeasWidget(self):
        if not self.ana_measw:
            self.ana_measw = sharedWidgets.MeasWidget(self.ana_pltw.getPlotItem(),"fft")
            self.ana_measw.setHidden(True)
        return self.ana_measw