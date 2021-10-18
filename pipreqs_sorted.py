from pipreqs.pipreqs import docopt, __doc__, __version__, init
import os
import os.path as op


def main():
    wd = op.dirname(__file__)
    dst = op.join(wd, "requirements.txt")

    try:
        os.remove(dst)
    except FileNotFoundError:
        pass

    # this is a copy of the pipreqs main fcn, but we pass our own argv to docopt
    args = docopt(__doc__, argv=[], version=__version__)
    init(args)

    unsorted = open(dst, "r").readlines()
    sortedlst = sorted(unsorted)
    open(dst, "w").write("".join(sortedlst))


if __name__ == "__main__":
    main()
