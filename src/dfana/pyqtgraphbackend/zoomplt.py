from dfana.sharedfuns import getFixedLenString
import numpy as np

name = "zoom"
iconName = "zoom"


class PltHandler:
    def __init__(self, data, dst):
        self.data = data
        self.dst = dst

    def initialize(self):
        plt = self.dst
        src = self.data["datasrc"]
        xname = src.axes["bottom"]["item"].label.toPlainText()
        plt.setLabel("bottom", xname)
        plt.setTitle("Zoom")
        plt.customlegend.layout.itemAt(1, 1).setText(xname)
        srccurves = src.curves
        L = len(srccurves)
        for idx, cu in enumerate(srccurves):
            plt.plot(x=[0], y=[0], name=cu.name(), pen=(idx + 1, L))

    def updateData(self, reg):
        x0, x1 = reg
        plt = self.dst
        src = self.data["datasrc"]
        xname = src.axes["bottom"]["item"].label.toPlainText()
        s0 = getFixedLenString(x0)
        s1 = getFixedLenString(x1)
        plt.setTitle(f"Zoom on {xname}: {s0} -- {s1}")
        for idx, curve in enumerate(src.curves):
            x = curve.xData
            y = curve.yData
            mask = np.logical_and(x >= x0, x <= x1)
            plt.curves[idx].setData(x=x[mask], y=y[mask])
