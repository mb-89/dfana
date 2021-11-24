from pyqtgraph.Qt import QtCore, QtGui, QtWidgets
import pyqtgraph as pg
import sys
import os.path as op
import pandas
import inspect
import webbrowser
import io
import logging
import datetime
import demjson

log = logging.getLogger()

sys.path.append(op.dirname(__file__))
import __parser__

class Parser(__parser__.Parser):
    def accept(self):
        return self.path.endswith(".csv")

    def parse_raw(self, read_csv_args=None,peekfile=True):
        if read_csv_args is None:
            if peekfile:
                firstline = open(self.path,"r").readline()
                if firstline.startswith("#format:"):
                    firstline = firstline.replace("#format:","")
                    try:read_csv_args = demjson.decode(firstline)
                    except: read_csv_args=None
        if read_csv_args is None:
            mp = CsvParserGUI(self,self.path)
            mp.exec_()
            read_csv_args = mp.result
            if read_csv_args is None: return []
            if read_csv_args == -1:self.parse_raw(peekfile=False)
        try:
            if 'filepath_or_buffer' in read_csv_args: read_csv_args.pop('filepath_or_buffer')
            df = pandas.read_csv(self.path,**read_csv_args)
        except UnicodeError as ue:
            read_csv_args["encoding"] = "latin-1"
            return self.parse_raw(read_csv_args,peekfile=False)
        except Exception as e:
            log.error(f"error during parsing: {str(e)}")
            return self.parse_raw(peekfile=False)
        
        metadata = self.collectMetadata(self.path)
        if "name" not in metadata:
            metadata["name"] = op.splitext(op.basename(self.path))[0]
        for k,v in metadata.items():
            df.attrs[k]=v

        df.drop(df.filter(regex="Unname"),axis=1, inplace=True)
        if df.columns.nlevels >1:df.columns = ['_'.join((x.replace("_","") for x in col)) for col in df.columns]

        return [df]

    def collectMetadata(self, path):
        metadata={"mtime": str(datetime.datetime.fromtimestamp(op.getmtime(path)))}
        return metadata


class CsvParserGUI(QtWidgets.QDialog):
    def __init__(self, parent,path):
        super().__init__()
        pg.mkQApp()
        self.parent = parent
        self.path = path
        self.result = None
        self.setWindowTitle(f"configure csv dissector for {path}")
        self.resize(800,600)

        fulldoc = inspect.getdoc(pandas.read_csv)
        params = inspect.signature(pandas.read_csv)
        paramsFromFulldoc = self.extractParamDesc(fulldoc,params)
        l = QtWidgets.QVBoxLayout()
        self.setLayout(l)

        help  = QtWidgets.QHBoxLayout()
        help.addWidget(QtWidgets.QLabel("Enter parameters for pandas.read_csv:"))#
        helpbutton = QtWidgets.QPushButton()
        helpbutton.setText("?")
        helpbutton.setMaximumWidth(50)
        helpbutton.clicked.connect(lambda: webbrowser.open("https://pandas.pydata.org/pandas-docs/stable/reference/api/pandas.read_csv.html",2))
        help.addWidget(helpbutton)
        l.addLayout(help)

        LNS = 25

        rawtxt = QtWidgets.QTreeView()
        rawMdl = QtGui.QStandardItemModel()
        rawtxt.setMaximumHeight(300)
        rawMdl.setColumnCount(1)
        rawtxt.setModel(rawMdl)
        rawtxt.setHeaderHidden(True)
        rawtxt.resizeColumnToContents(0)
        args_from_file={}
        self.txt=""
        with open(self.path,"r") as f:
            for idx in range(LNS):
                line = next(f)
                if idx==0:
                    if line.startswith("#format:"):
                        firstline = line.replace("#format:","")
                        try:args_from_file = demjson.decode(firstline)
                        except: pass
                item = QtGui.QStandardItem(line.strip())
                self.txt+=line
                item.setEditable(False)
                rawMdl.appendRow([item])

        paramwidget = QtWidgets.QTableWidget()
        paramwidget.setColumnCount(2)
        paramwidget.setRowCount(len(params.parameters))
        paramwidget.setVerticalHeaderLabels([x.name for x in params.parameters.values()])
        paramwidget.setHorizontalHeaderLabels(["value", "description"])
        l.addWidget(paramwidget)
        l.addWidget(QtWidgets.QLabel(f"raw txt lines: (first {LNS})"))

        for idx,(k,p) in enumerate(params.parameters.items()):
            ed = QtWidgets.QLineEdit("")
            ed.textEdited.connect(self.parse)
            deftxt = str(p.default) if (p.default != inspect._empty) else ""
            desc = p.annotation if isinstance(p.annotation,str) else paramsFromFulldoc.get(k,"")
            ed.setPlaceholderText(deftxt)
            if k in args_from_file:
                ed.setText(str(args_from_file[k]))
            qdesc = QtWidgets.QLineEdit(desc)
            qdesc.setCursorPosition(0)

            paramwidget.setCellWidget(idx,0,ed)
            paramwidget.setCellWidget(idx,1,qdesc)
        
        paramwidget.cellWidget(0,0).setText(path)
        paramwidget.resizeColumnToContents(0)
        paramwidget.horizontalHeader().setStretchLastSection(1)
        self.params = paramwidget

        l.addWidget(rawtxt)
        l.addWidget(QtWidgets.QLabel(f"parsed txt lines (first {LNS}):"))

        parsemdl = QtGui.QStandardItemModel()
        parsedtxt = QtWidgets.QTreeView()
        parsedtxt.setModel(parsemdl)
        parsedtxt.setMaximumHeight(300)

        self.parsemdl =parsemdl
        self.parsedtxt =parsedtxt
        l.addWidget(parsedtxt)

        l.addItem(QtWidgets.QSpacerItem(5,5,QtWidgets.QSizePolicy.Expanding,QtWidgets.QSizePolicy.Expanding))

        self.rowsAndCols = QtWidgets.QLabel("")
        self.ok = QtWidgets.QPushButton("parse")
        self.respec = QtWidgets.QPushButton("add format spec to file and reload")
        self.cancel = QtWidgets.QPushButton("cancel")
        self.cancel.clicked.connect(self.reject)
        self.ok.clicked.connect(self.accept)
        self.respec.clicked.connect(self.respecfun)
        self.cancel.setFocusPolicy(QtCore.Qt.FocusPolicy.NoFocus)
        self.ok.setFocusPolicy(QtCore.Qt.FocusPolicy.NoFocus)
        self.respec.setFocusPolicy(QtCore.Qt.FocusPolicy.NoFocus)

        L2 = QtWidgets.QHBoxLayout()
        L2.setContentsMargins(0,0,0,0)
        L2.setSpacing(0)
        L2.addItem(QtWidgets.QSpacerItem(5,5,QtWidgets.QSizePolicy.Expanding,QtWidgets.QSizePolicy.Expanding))
        L2.addWidget(self.rowsAndCols)
        L2.addWidget(self.cancel)
        L2.addWidget(self.ok)
        L2.addWidget(self.respec)
        l.addLayout(L2)

        self.show()
        self.raise_()
        self.activateWindow()
        self.parse()

    def extractParamDesc(self,txt,params):
        lines = txt.split("\n")
        paragraphs = []
        pdict = {}
        inparagraph=False
        pstart = 0
        pend = 0
        for idx, line in enumerate(lines[:-1]):
            if inparagraph and not line.startswith(" ") and bool(line):
                pend = idx
                paragraphs.append((pstart,pend))
                inparagraph=False
            if not inparagraph and not line.startswith(" ") and lines[idx+1].startswith(" ") and lines[idx+1]:
                inparagraph = True
                pstart = idx
        for p in paragraphs:
            ptext = lines[p[0]:p[1]]
            p0split = ptext[0].split(":")
            p0split[-1]+=(".")
            if len(p0split)<2:p0split.append("")
            pname = p0split[0].strip()
            pdesc = p0split[1].strip()+" "+" ".join(x.strip() for x in ptext[1:])
            pdict[pname]=pdesc
        return pdict

    def parse(self):
        try:self.parsemdl.clear()
        except:return
        self.ok.setEnabled(False)
        self.rowsAndCols.setText("")
        sig = inspect.signature(pandas.read_csv)
        keys = tuple(sig.parameters.keys())
        dct = {}
        for idx in range(self.params.rowCount()):
            entry = self.params.cellWidget(idx,0).text()
            param = sig.parameters[keys[idx]]
            if entry != "":
                if (param.annotation != inspect._empty) and isinstance(entry,str):dct[param.name] = entry
                else:
                    try: dct[param.name] = eval(entry)
                    except:pass
        dct['filepath_or_buffer'] = io.StringIO(self.txt)
        self.result = dict((k,v) for k,v in dct.items())
        fp = dct.pop('filepath_or_buffer')
        try: df = pandas.read_csv(fp, **dct)
        except Exception as e:
            log.error(f"error during parsing: {str(e)}")
            return
        if df.columns.nlevels >1:
            df.columns = ['_'.join((x.replace("_","") for x in col)) for col in df.columns]
        self.parsemdl.setHorizontalHeaderLabels(df.columns)
        L=len(df.columns)
        self.parsemdl.setColumnCount(L)
        for idx, row in df.iterrows():
            QtRow = [QtGui.QStandardItem(str(x).strip()) for x in row]
            self.parsemdl.appendRow(QtRow)
        
        self.rowsAndCols.setText(f"found {L} cols of data (before postprocessing) ")
        self.ok.setEnabled(L)
        for idx in range(L):
            self.parsedtxt.resizeColumnToContents(L-1-idx)

    def respecfun(self):
        res = self.result
        if 'filepath_or_buffer' in res: res.pop('filepath_or_buffer')
        if not res: 
            self.result=-1
            self.accept()
        if "skiprows" in res: res["skiprows"]+=1
        else:res["skiprows"]=1
        tmp = open(self.path,"rb").read()
        open(self.path,"wb").write(b"#format:"+bytes(demjson.encode(res), encoding="utf-8")+b"\n"+tmp)
        self.result=-1
        self.accept()


    def reject(self):
        self.result = None
        super().reject()

    def accept(self):
        super().accept()
