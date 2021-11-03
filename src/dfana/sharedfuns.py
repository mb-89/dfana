import numpy as np

numValLen = 8


def getFixedLenString(flt, L=numValLen):

    s = np.format_float_scientific(flt, precision=L - 5, trim="-")
    return s
