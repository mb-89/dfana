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
    def ana_show(self, show):
        setHidden = not show
        self.ana_region.setVisible(show)
        super().ana_show(show)

    def ana_getWidget(self):
        if not self.ana_widget:
            plt = sharedWidgets.PlotWithMeasWidget(parent=self)
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
        freqplt = self.ana_widget.pw
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
            if buildplots:freqplt.plot(x=xf[1:],y=yf[1:],pen=curve.opts['pen'],name=name)
            else: pi.curves[idx].setData(x=xf[1:],y=yf[1:])
