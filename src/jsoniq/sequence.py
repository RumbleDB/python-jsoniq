from pyspark import RDD
from pyspark.sql import SparkSession
import json

class SequenceOfItems:
    def __init__(self, sequence, sparkcontext):
        self._jsequence = sequence
        self._sparkcontext = sparkcontext

    def getAsJSONList(self):
        return [json.loads(l.serializeAsJSON()) for l in self._jsequence.getAsList()]

    def getAsJSONRDD(self):
        rdd = self._jsequence.getAsStringRDD();
        print("Strings:");
        for s in rdd.take(10):
            print(s);
        rdd = RDD(rdd, self._sparkcontext)
        return rdd.map(lambda l: json.loads(l))

    def nextJSON(self):
        return self._jsequence.next().serializeAsJSON()

    def __getattr__(self, item):
        return getattr(self._jsequence, item)