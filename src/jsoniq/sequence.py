from pyspark.sql import SparkSession
import json

class SequenceOfItems:
    def __init__(self, sequence):
        self._jsequence = sequence

    def getAsJSONList(self):
        for s in self._jsequence.getAsList():
            print(s.serialize());
        return [json.loads(l.serialize()) for l in self._jsequence.getAsList()]

    def __getattr__(self, item):
        print(f"Accessing attribute: {item}")
        return getattr(self._jsequence, item)