from PySide6 import QtCore
from pandas import DataFrame
from numpy import diff, median
from pandas.api.types import is_string_dtype,is_bool_dtype
import numpy as np
import pandas as pd
import itertools
import os.path as op

#https://stackoverflow.com/a/62027329
class Signaller(QtCore.QObject):
    done = QtCore.Signal(dict)

dfcnt = 0

class Parser(QtCore.QRunnable):
    def __init__(self,path,tempdir=None):
        super().__init__()
        self._signaller = Signaller()
        self.path = path
        self.accepted = self.accept()
        self.consumedPaths = self.consumePaths()
        self.tempdir = tempdir

    @property
    def signaller(self):
        return self._signaller

    def accept(self):
        return False
    def consumePaths(self):
         return [self.path]

    def parse_raw(self):
        return []

    def postprocess(self, dfs):
        global dfcnt
        PP = Postprocessor()
        for df in dfs:
            df.attrs["_idx"] = f"DF{str(dfcnt).zfill(3)}"
            #fill in mandatory metadata, if not present:
            if "name" not in df.attrs: df.attrs["name"] = df.attrs["_idx"]
            dfcnt+=1
        PP.process(dfs)
        return  [x for x in dfs if not x.empty]

    def run(self):
        dfs_raw = self.parse_raw()
        dfs = self.postprocess(dfs_raw)
        self.signaller.done.emit({"path":self.path, "result": dfs})

class Postprocessor():
    RAWCOLS = ["roh","raw"]
    def process(self, dfs, splitChunks=True):
        self.cleanupNames(dfs)
        self.cleanupTimeCol(dfs)
        self.setUnits(dfs)
        for df in dfs: df.fillna(0,inplace=True)
        dfs = [item for sublist in [self.chunk(x, splitChunks) for x in dfs] for item in sublist] #flattened list of lists
        self.putConstColsInMetadata(dfs)
        self.convertDatatypesToInts(dfs)
        self.addMiscMetadata(dfs)


        return [x for x in dfs if not x.empty]

    def convertDatatypesToInts(self, dfs):
        for df in dfs:
            for col in df.columns:
                if col.endswith("text"):
                    if is_string_dtype(df[col]):
                        df[col] = [0 for _ in df[col]]
                elif is_bool_dtype(df[col]):
                        df[col] = [int(x) for x in df[col]]

    def setUnits(self, dfs):
        pass

    def cleanupNames(self, dfs):
        for df in dfs:
            cleancols = [x.replace("_","/").lower() for x in df.columns]
            for raw in self.RAWCOLS: cleancols = [x.replace("/"+raw,"") for x in cleancols]
            df.columns = cleancols

            cols = list(df.columns)

            #we reduce the name depth of the columns by removing all common prefixes:
            while True:
                splitcols = [x.split("/") for x in cols]
                starts = [x[0] for x in splitcols]
                pops = [x for x in starts if starts.count(x)==1]
                for p in pops: starts.remove(p)
                rems = set(starts)
                remcnt = 0
                for rem in rems:
                    for splitcol in splitcols:
                        if splitcol[0] == rem: 
                            splitcol.pop(0)
                            remcnt+=1
                if remcnt == 0:break
                if len(set(tuple(tuple(x) for x in splitcols)))<len(cols): break
                cols = ["/".join(x) for x in splitcols]
            
            df.rename(columns=dict(zip(df.columns, cols)),inplace=True)

    def cleanupTimeCol(self, dfs):
        for df in dfs:
            timecol = None
            fak = 1

            if "time/datetime"              in df:  timecol = "time/datetime";              fak = 60.0*60.0*24.0
            elif "time/datetime/raw"        in df:  timecol = "time/datetime/raw";          fak = 60.0*60.0*24.0
            elif "rt/time/datetime/date"    in df:  timecol = "rt/time/datetime/date";      fak = 60.0*60.0*24.0
            elif "rt/time/datetime"         in df:  timecol = "rt/time/datetime";           fak = 60.0*60.0*24.0
            elif "time/datumuhrzeit"        in df:  timecol = "time/datumuhrzeit";          fak = 60.0*60.0*24.0
            elif "time/date & time"         in df:  timecol = "time/date & time";           fak = 60.0*60.0*24.0
            elif "time/s"                   in df:  timecol = "time/s"
            elif "time"                     in df:  timecol = "time"
            elif "time/ms"                  in df:  timecol = "time/ms";                    fak = 1e-3
    
            dateInMultiCols = (df.columns[0] == "date" and df.columns[1] == "time" and df.columns[2] == "ms")
    
            if dateInMultiCols:
                datestr = df["date"]+df["time"]+df["ms"].astype(int).astype(str).str.zfill(3) #we cut the fractional milliseconds for now
                dates   = pd.to_datetime(datestr, format="%m/%d/%Y%H:%M:%S %p%f").astype('int64')*(10**-9)
                df.drop(["date","time","ms"], axis=1,inplace=True)
                df["time"] = dates
                timecol = "time"

            if timecol:
                offset = df[timecol].iloc[0]
                df[timecol] -= offset
                df[timecol] *= fak
                df.rename(columns={timecol: 'time/s'},inplace=True)
                df.set_index("time/s",inplace=True)
                if not df.index.is_monotonic:
                    df.sort_index(inplace=True)

    def chunk(self, df, splitChunks=True):
        dfdiff = diff(df.index)
        meddiff = median(dfdiff)
        dfs = []

        if splitChunks:
            splits = []
            for idx,x in enumerate(dfdiff): 
                if x>10.0*meddiff: splits.append(idx+1)
            start = 0
            idx = 0
            for end in splits:
                chunk = df.iloc[start:end,:]
                dfs.append(chunk)
                chunk.attrs["name"] = df.attrs["name"]+f".{idx}"
                chunk.index = chunk.index-chunk.index[0]
                idx+=1
                start = end
    
        if not dfs: dfs = [df]
        for df in dfs: df.attrs["_ts"] = median(diff(df.index))

        return dfs

    def putConstColsInMetadata(self, dfs):
        for df in dfs:
            constcols = tuple(x for x in df.columns if df[x].nunique()==1)
            for cc in constcols:
                name = cc
                val = df[name].iloc[0]
                if name in df.attrs: name="col_"+name
                df.attrs[name] = val
                #df.drop(columns=[cc], inplace=True) #dont drop. its confusing when browsing the dfs

    def addMiscMetadata(self, dfs):
        for df in dfs:
            df.attrs["mem"] = df.memory_usage(index=True).sum()
            df.attrs["rows"] = len(df)
            df.attrs["cols"] = len(df.columns)+1