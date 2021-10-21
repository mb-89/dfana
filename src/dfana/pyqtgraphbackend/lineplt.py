import pyqtgraph as pg


class Plt(pg.GraphicsLayoutWidget):
    def __init__(self, data, **kwargs):
        super().__init__()
        if data.empty:
            return
        xdata = data.index.values
        xname = data.index.name if data.index.name else "idx"
        plt = self.addPlot()
        plt.addLegend()
        plt.showGrid(1, 1, int(0.75 * 255))
        L = len(data.columns)
        plt.setLabel("bottom", xname)
        for idx, yname in enumerate(data.columns):
            plt.plot(x=xdata, y=data[yname], name=yname, pen=(idx + 1, L))
