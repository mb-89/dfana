from dfana import dfana
import itertools


def test_differentLoadTypes():
    assert isinstance(dfana.getExampleNames()[0], str)

    # loading via the command line
    assert dfana.main(["test", "example_stepresponses1", "--nonblock"]) == 0

    # loading via the load and plot fcns
    examples = dfana.getExampleNames()
    dfs = dfana.load(examples[0])
    dfana.plot(dfs[0])
    dfana.showPlots(block=False)


def test_AllBackends():
    backends = dfana.getAvailableBackends()
    examples = tuple(dfana.load(x) for x in dfana.getExampleNames())

    if len(backends) > len(examples):
        combis = [(i, j) for i, j in zip(backends, itertools.cycle(examples))]
    else:
        combis = [(i, j) for i, j in zip(itertools.cycle(backends), examples)]

    for b, e in combis:
        _ = dfana.plot(e[0], backend=b, show=True, block=False)
