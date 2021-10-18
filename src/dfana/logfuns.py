import logging
import sys

log = logging.getLogger("dfana")


def setupLogging():
    if log.handlers:
        return -1

    log.setLevel(logging.DEBUG)
    formatter = logging.Formatter("%(relativeCreated)08d %(levelname)s: %(message)s")
    log._fmt = formatter

    logging.addLevelName(logging.DEBUG, "DBG ")
    logging.addLevelName(logging.INFO, "INFO")
    logging.addLevelName(logging.WARNING, "WARN")
    logging.addLevelName(logging.ERROR, "ERR ")

    # add to console
    ch = logging.StreamHandler(sys.stdout)
    ch.setLevel(logging.DEBUG)
    ch.setFormatter(log._fmt)
    log.addHandler(ch)

    return 0
