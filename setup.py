import setuptools
import shutil
import configparser

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

try:
    import pipreqs_sorted

    pipreqs_sorted.main()
except ModuleNotFoundError:
    pass

cfg = configparser.ConfigParser()
cfg.read("setup.cfg")

dct = {}
for s in cfg.sections():
    if s not in ["metadata", "options"]:
        continue
    for k, v in cfg[s].items():
        dct[k] = v

dct["long_description"] = long_description
dct["long_description_content_type"] = "text/markdown"
dct["package_dir"] = {"": "src"}
dct["packages"] = setuptools.find_packages(where="src")
dct["install_requires"] = open("requirements.txt", "r").readlines()
dct["include_package_data"] = True

setuptools.setup(**dct)
shutil.rmtree("build", ignore_errors=True)
shutil.rmtree(f"src/{dct['name']}.egg-info", ignore_errors=True)
