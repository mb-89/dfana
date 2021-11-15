import logging
from string import Template
from pylatex import utils
import pyperclip
log = logging.getLogger()
DOWNSAMPLE = 500

def export(name, plotwidget):
    plotDataDict = {}
    widgets = plotwidget.widgets[0]
    for idx in range(widgets.count()):
        w = widgets.widget(idx).pw.pw
        pi = w.getPlotItem()
        plotDataDict[idx] = getPlotData(w)
    hsum = sum(x["h_abs"] for x in plotDataDict.values())
    for x in plotDataDict.values():
        x["h_rel"] = x["h_abs"]/hsum
    createLaTexFile(plotDataDict)

def getPlotData(w):
    pi = w.getPlotItem()
    data = {}
    data["h_abs"] = w.height()
    data["xlabel"] = pi.axes["bottom"]["item"].label.toPlainText()
    data["ylabel"] = pi.axes["left"]["item"].label.toPlainText()
    data["xrange"] = pi.axes["bottom"]["item"].range
    data["yrange"] = pi.axes["left"]["item"].range

    curves = []
    for c in pi.curves:
        cdict = {}
        cdict["name"] = c.name()
        cdict["xdata"] = c.xDisp
        cdict["ydata"] = c.yDisp
        curves.append(cdict)
    data["curves"] = curves
    return data

def createLaTexFile(plotDataDict):
    axes = []
    for idx,subplt in plotDataDict.items():
        axisstr = r"\begin{axis}[at={(0,-"+ f"{idx*5}"+r"cm)},cycle list name=Dark2,width=.8\textwidth, height=5cm, hide y axis,axis x line*=bottom,legend pos=outer north east]"+"\n"
        names = [str(utils.escape_latex(x["name"])) for x in subplt["curves"]]
        coords= []
        coordstring = ""
        for c in subplt["curves"]:
            coords= []
            L = len(c["xdata"])
            ds = (L//DOWNSAMPLE)+1
            for x,y in zip(c["xdata"][::ds],c["ydata"][::ds]):
                coords.append(f"({x},{y})")
            coordstring+=(r"\addplot+[thick] coordinates {"+"".join(coords)+"};\n")
        legendstring=r"\legend{"+"\n"+",\n".join(names)+"\n}\n"

        axisstr+=coordstring
        axisstr+=legendstring

        axisstr+=r"\end{axis}"
        axes.append(axisstr)

    T = Template(LATEXTEMPLATE)
    txt = T.substitute(AXES="\n".join(axes))
    pyperclip.copy(txt)
    log.info("copied LaTeX code to clipboard.")


LATEXTEMPLATE = r"""\documentclass[crop,tikz,class=memoir,oldfontcommands,10pt]{standalone}
\usepackage[T1]{fontenc}%
\usepackage[english]{babel}%
\usepackage[final]{microtype}%
\usepackage{dejavu}%
\usepackage{pgfplots}
\usepackage{sansmath}
\usetikzlibrary{colorbrewer}
\usepgfplotslibrary{colorbrewer}
\usetikzlibrary{matrix}
%uncomment here to load style information from external files --------------------------------------
%\newcommand*{\autogenpath}{../autogen}
%\input{\autogenpath/tikzmacros}
%\input{\autogenpath/pgfplotsmacros}
%---------------------------------------------------------------------------------------------------
\pgfplotsset{
  cycle list/Dark2
}

\begin{document}
\begin{tikzpicture}

$AXES

\end{tikzpicture}
\end{document}"""