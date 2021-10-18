#About the setup system
* setup.py will automatically build requirements.txt, using pipreqs, and also use it for its own requirements.
* to install the package, run "pip install ." in this directory
* to install the package in editable mode, run "pip install -e ." (for devs)
* to build the wheel-file for this package, run "py -m build" in this folder. 

* uses black and flake8 for linting (they are also part of the pre-commit hook)
* uses pytest for testing (#TODO: make pytest part of pre-push and maybe even github actions)

See also: https://www.youtube.com/watch?v=DhUpxWjOhME

#Sidenotes
* If you want to debug tests, you need to disable the coverage module. It interferes with the
VSCode test debugger (remove "--cov=dfana --cov-report term-missing -v" in pyproject.toml)