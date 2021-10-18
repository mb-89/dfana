from dfana import dfana


def test_main():
    assert dfana.main(["test", "example_stepresponses1", "--nonblock"]) == 0
