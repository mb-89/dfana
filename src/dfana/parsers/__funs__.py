from glob import glob
import os.path as op
import importlib 
import py7zr
import shutil
import tempfile
import logging
log = logging.getLogger()

#https://stackoverflow.com/a/59305379
try:    shutil.register_unpack_format('7zip', ['.7z'], py7zr.unpack_7zarchive)
except  shutil.RegistryError:   pass
try:    shutil.register_archive_format('7zip', py7zr.pack_7zarchive)
except  shutil.RegistryError:   pass

def getParsers():
    parsers = {}
    modules = glob(op.join(op.dirname(__file__), "*.py"))
    modules = [(op.splitext(op.basename(f))[0],f) for f in modules if op.isfile(f) and not op.basename(f).startswith("_")]
    for mname, mfile in modules:
        spec = importlib.util.spec_from_file_location(mname, mfile)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        try:parser = module.Parser
        except: pass
        parsers[mname] = parser
    return parsers

parsers = getParsers()

def prepare(path):
    pendingfiles = set((x,None) for x in glob(path, recursive="**" in path) if op.isfile(x))
    #if a file happens to be an archive, 
    #extract it to a temp dir and run over that
    while(pendingfiles):
        nextfile, td = pendingfiles.pop()
        #dealing with archives
        if td is None:
            td = tempfile.TemporaryDirectory()
            try:
                shutil.unpack_archive(nextfile, td.name)
                log.info(f"unpacked {nextfile} to {td.name}")
            except (ValueError, shutil.ReadError) as _:
                td.cleanup()
                td = None
            else:
                subpath = td.name+"/**/*"
                additionalFiles = set((x,td) for x in glob(subpath, recursive="**" in subpath) if op.isfile(x))
                pendingfiles |= additionalFiles
                pendingfiles.discard(nextfile)
                continue

        #dealing with files
        for P in parsers.values():
            p = P(nextfile, td)
            if p.accepted:
                for cp in p.consumedPaths:
                    pendingfiles.discard(cp)
                yield p
