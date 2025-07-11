from pyspark.sql import SparkSession
import json

class SequenceOfItems:
    def __init__(self, sequence):
        self._jsequence = sequence

    def getAsJSONList(self):
        return [json.loads(l.serializeAsJSON()) for l in self._jsequence.getAsList()]

    def nextJSON(self):
        return self._jsequence.next().serializeAsJSON()

    def __getattr__(self, item):
        return getattr(self._jsequence, item)