from abc import ABC, abstractmethod


class AbstractExample(ABC):
    @abstractmethod
    def createDF(self):
        """creates the dataframe that contains the example data"""
