from glob import glob
import os.path as op
import importlib 

def getFuns():
    anas = {}
    modules = glob(op.join(op.dirname(__file__), "*.py"))
    modules = [(op.splitext(op.basename(f))[0],f) for f in modules if op.isfile(f) and not op.basename(f).startswith("_")]
    for mname, mfile in modules:
        spec = importlib.util.spec_from_file_location(mname, mfile)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        try:
            ana = module.Ana
            anas[mname] = ana
        except: pass
        
    return anas