import sys
import os.path as op
sys.path.append(op.dirname(__file__))
import __parser__

class Parser(__parser__.Parser):
    def accept(self):
        return self.path.endswith(".csv")