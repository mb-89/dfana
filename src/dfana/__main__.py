try:  # pragma: no cover
    from dfana.dfana import main
    from dfana.logfuns import setupLogging
except ModuleNotFoundError:  # pragma: no cover
    # we need this so the vscode debugger works better
    from dfana import main
    from logfuns import setupLogging

import sys  # pragma: no cover

setupLogging()  # pragma: no cover
main(sys.argv)  # pragma: no cover
