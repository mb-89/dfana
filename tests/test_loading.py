from dfana import dfana


def test_differentLoadTypes():
    assert isinstance(dfana.getExampleNames()[0], str)
    assert dfana.main(["test", "example_stepresponses1", "--nonblock"]) == 0

    examples = dfana.getExampleNames()
    dfs = dfana.load(examples[0])
    dfana.plot(dfs[0])
    dfana.showPlots(block=False)
