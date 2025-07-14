from pyspark import RDD
from pyspark.sql import SparkSession
import json

class SequenceOfItems:
    def __init__(self, sequence, sparkcontext):
        self._jsequence = sequence
        self._sparkcontext = sparkcontext

    def json(self):
        return [json.loads(l.serializeAsJSON()) for l in self._jsequence.items()]

    def rdd(self):
        rdd = self._jsequence.getAsPickledStringRDD();
        rdd = RDD(rdd, self._sparkcontext)
        return rdd.map(lambda l: json.loads(l))

    def nextJSON(self):
        return self._jsequence.next().serializeAsJSON()

    def __getattr__(self, item):
        return getattr(self._jsequence, item)