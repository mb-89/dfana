import pyqtgraph.dockarea as da
import pyqtgraph as pg
import logging
import helperfuns
import math
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
        for idx,(xd,yd) in enumerate(pltdata):
            plt = self.buildplot(xd,yd)
            self.addWidget(plt,row=idx,col=0)

    def buildplot(self, xd,yd):
        pw = XYplot()
        plt = pw.getPlotItem()
        xname = list(xd.keys())[0]
        plt.addLegend()
        plt.setLabel("left", xname)
        xdata = xd[xname]
        l = len(yd)
        for idx,(yname, ydata) in enumerate(yd.items()):
            try:
                plt.plot(x=xdata,y=ydata,pen=(idx,l), name=yname)
            except:
                log.error(f"could not plot column {name}")
                continue
        return pw

class XYplot(pg.PlotWidget):
    def __init__(self):
        super().__init__()
    def toggle(self):
        self.setHidden(not self.isHidden())
