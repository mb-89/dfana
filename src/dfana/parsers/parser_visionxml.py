import sys
import os.path as op
sys.path.append(op.dirname(__file__))
import __parser__
from lxml import etree
from datetime import datetime
import numpy as np
import pandas as pd

class Parser(__parser__.Parser):
    def accept(self):
        self.datadir = None
        if not self.path.endswith(".xml"):return False
        rootxml = etree.parse(self.path).getroot()
        datadir = op.splitext(self.path)[0]
        isVisionXML = rootxml.tag == "DataSet" or rootxml.tag == "DataMatrix" and op.isdir(datadir)
        if not isVisionXML:return False
        self.datadir = datadir
        self.rootxml = rootxml
        return True

    def consumePaths(self):
        return [self.path, self.datadir] if self.datadir else [self.path]

    def parse_raw(self):
        dfs = self.analyzevisionxml(self.rootxml)
        return dfs


    def analyzevisionxml(self, rootxml):
        dataframes = []
        #first, clean up the xml and resolve all children:
        xml = rootxml.find("VisionStructure")
        self._recursiveResolveXMLchildren(xml)

        #get all mass data files
        massData = []
        for record in (x for x in xml.iter("AssociatedRecord") if x.find("Name").text == "MassData"):
            path = [record.find("RecordRef").text]
            target = record.getparent()
            columnInfo = target.getparent().find("Private").find("Columns")
            while target != xml:
                nameelem = target.find("RecordRef")
                if nameelem is not None:
                    path.append(op.dirname(target.find("RecordRef").text))
                target=target.getparent()
            basepath = rootxml.base
            if not op.isfile(basepath):basepath=basepath[6:]#convert uri to path
            path = op.join(op.dirname(basepath), *reversed(path)).replace("%20", " ")
            if op.isfile(path) and op.getsize(path):
                massData.append((path,columnInfo))

        #parse all data matrices
        L = len(massData)
        mtimestr = rootxml.findtext("VisionStructure/Administration/Modified/DateTime")
        mtimefixed = str(datetime.strptime(mtimestr,"%Y-%m-%dT%H:%M:%S.%f"))
        metadata = {
            "name": rootxml.findtext("VisionStructure/Administration/Name").replace("/","").replace(":",""),
            "mtime": mtimefixed
            }
        idx = 0
        for f, cols in massData:
            basename = op.basename(op.dirname(f))
            dtypes = self.getdtypes(cols)
            isLogData = cols.findtext("../LogPeriod") is not None
            data = np.fromfile(f, dtype=dtypes)
            df = pd.DataFrame(data)
            for x in df.columns:
                if x.startswith("$pad"):
                    del df[x]

            txts = [x for x in df.columns if x.endswith("_Text")]
            if txts:
                strf = f.replace("MassData.bin","Strings.bin")
                if op.isfile(strf): 
                    self.translateTxts(df, txts, strf)
                else: 
                    for txt in txts: df.pop(txt)

            if isLogData: dataframes.append(df)
            else: #if the data is not logdata, it contains metadata. in that case, add the metadata to df.attrs
                for k in df.columns[1:]:
                    metadata[k] = df[k][0]

        if metadata:
            for df in dataframes:
                df.attrs.update(metadata)

        return dataframes

    def translateTxts(self, df, txtcols, strf):
        strdump=open(strf,"rb").read()
        N=256
        allstrings=[strdump[i:i+N].decode("utf-16").rstrip("\x00\x00") for i in range(0, len(strdump), N)]
        for col in txtcols:
            try:df[col] = [allstrings[x-2] for x in df[col].values]
            except IndexError:
                pass#this happens for example when the strings are empty
            df[col] = df[col].astype(pd.StringDtype())

    def getdtypes(self, cols):
        dtypeListlist = []
        dt = np.dtype([('a', 'i4'), ('b', 'i4'), ('c', 'i4'), ('d', 'f4'), ('e', 'i4'),
                    ('f', 'i4', (256,))])

        colnames = []
        nrOfplaceHolders = 0
        for col in cols.iter("Column"):

            quantityName = col.find("Quantity").text
            signame = col.find("Signal").text.replace("\\","").replace("_","/")
            if signame in colnames: quantityName = "IGNORE"
            else:                   colnames.append(signame)
            unit = col.find("Unit").text
            fullname = signame+"_"+quantityName+"_"+unit
            if   quantityName is None:
                raise UserWarning("invalid rawdata")

            elif quantityName == "Logical":
                dtypeListlist.append((fullname,'b'))
                dtypeListlist.append((f"$pad{nrOfplaceHolders}",'V7'))
                nrOfplaceHolders+=1
                #mask="b7x"

            elif quantityName in ["Integer", "Integer Flag"]:
                dtypeListlist.append((f"$pad{nrOfplaceHolders}",'V4'))
                dtypeListlist.append((fullname,'i4'))
                nrOfplaceHolders+=1

            elif quantityName in ["Text", "Text"]:
                dtypeListlist.append((fullname,'i4'))
                dtypeListlist.append((f"$pad{nrOfplaceHolders}",'V4'))
                nrOfplaceHolders+=1

            else:
                type = np.dtype('d')
                dtypeListlist.append((fullname,type))

        return np.dtype(dtypeListlist)

    def _recursiveResolveXMLchildren(self, xml):
        for ch in list(xml.iterchildren("Child")):
            base = xml.base
            if not op.isfile(base): base = xml.base[6:]
            file = op.join(op.dirname(base), ch.find("RecordRef").text)
            if not op.isfile(file): 
                file = file.replace("%20", " ")
            tmproot = etree.parse(file).getroot()
            chxml = tmproot
            #if not chxml: continue
            #tmproot.remove(chxml)
            namechild = etree.SubElement(chxml, "Name")
            namechild.text = ch.find("Name").text
            recordchild = etree.SubElement(chxml, "RecordRef")
            recordchild.text = ch.find("RecordRef").text
            xml.remove(ch)
            chxml.tag = namechild.text.replace(" ","").replace("~","")
            xml.append(chxml)