from dfana import dfana
from dfana import logfuns


def test_main():
    assert logfuns.setupLogging() == 0  # first pass for logging setup
    assert logfuns.setupLogging() == -1  # second pass: skipped bc already set up
    assert dfana.main(["test", "-v"]) == 0
    assert dfana.main(["test", "-?"]) == 0
