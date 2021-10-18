from glob import glob
import os.path as op
from functools import cache
from x2df import examples as x2dfx


@cache
def getClassDict():
    prefix = "example_"
    classes = {}
    mods = glob(op.join(op.dirname(__file__), "*.py"))
    mods = [f for f in mods if op.isfile(f) and op.basename(f).startswith(prefix)]
    mods = [(op.splitext(op.basename(f))[0], f) for f in mods]
    for (
        mname,
        mfile,
    ) in mods:  # this is ugly, but otherwise the coverage report doesnt find it...
        importname = f"dfana.examples.{mname}"
        exec("import " + importname)
        classes[mname.replace(prefix, "")] = eval(f"{importname}.Example")

    classes.update(x2dfx.getClassDict())

    return classes


def loadExample(examplename):
    dfs = []
    examplename = examplename.replace("example_", "")
    ex = getClassDict().get(examplename)
    if ex:
        dfs.append(ex().createDF())
    return dfs
