import configparser
from contextlib import redirect_stdout
import os.path as op
from src.dfana import dfana

# write version to source code
cfg = configparser.ConfigParser()
cfg.read("setup.cfg")
lines = ["# this file is autogenerated on pre-commit"]
lines.append('__version__ = "' + cfg["metadata"]["version"] + '"')
lines.append("")
open("src/dfana/__metadata__.py", "w").write("\n".join(lines))

# write cmdline help to file


with open(op.join(op.dirname(__file__), "README_CMDLINE"), "w") as f:
    with redirect_stdout(f):
        dfana.main(["-?"])
