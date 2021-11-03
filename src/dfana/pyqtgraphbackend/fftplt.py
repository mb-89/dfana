from dfana.sharedfuns import getFixedLenString
from scipy import fft
import numpy as np

name = "fft"
iconName = "fft"


class PltHandler:
    def __init__(self, data, dst):
        self.data = data
        self.dst = dst

    def initialize(self):
        plt = self.dst
        src = self.data["datasrc"]
        xname = "ℱ{" + src.axes["bottom"]["item"].label.toPlainText().strip() + "}"
        plt.setLabel("bottom", xname)
        plt.setTitle("FFT")
        plt.customlegend.layout.itemAt(1, 1).setText(xname)
        srccurves = src.curves
        L = len(srccurves)
        for idx, cu in enumerate(srccurves):
            plt.plot(x=[0, 1], y=[0, 1], name=cu.name(), pen=(idx + 1, L))

    def updateData(self, reg):
        x0, x1 = reg
        plt = self.dst
        src = self.data["datasrc"]
        xname = src.axes["bottom"]["item"].label.toPlainText()
        s0 = getFixedLenString(x0)
        s1 = getFixedLenString(x1)
        plt.setTitle(f"FFT on {xname}: {s0} -- {s1}")

        for idx, curve in enumerate(src.curves):
            x = curve.xData
            y = curve.yData
            mask = np.logical_and(x >= x0, x <= x1)
            x = x[mask]
            y = y[mask]
            N = len(x)
            try:
                T = (x[-1] - x[0]) / N
            except IndexError:
                continue
            yf = 2.0 / N * np.abs(fft.fft(y)[0 : N // 2])
            xf = np.linspace(0.0, 1.0 / (2.0 * T), N // 2)
            plt.curves[idx].setData(x=xf[1:], y=yf[1:])
