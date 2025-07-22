from pyspark import RDD
from pyspark.sql import SparkSession
from pyspark.sql import DataFrame
import json

class SequenceOfItems:
    def __init__(self, sequence, sparksession):
        self._jsequence = sequence
        self._sparkcontext = sparksession.sparkContext
        self._sparksession = sparksession

    def json(self):
        return tuple([json.loads(l.serializeAsJSON()) for l in self._jsequence.items()])

    def rdd(self):
        rdd = self._jsequence.getAsPickledStringRDD();
        rdd = RDD(rdd, self._sparkcontext)
        return rdd.map(lambda l: json.loads(l))

    def df(self):
        return DataFrame(self._jsequence.getAsDataFrame(), self._sparksession)

    def pdf(self):
        return self.df().toPandas()

    def nextJSON(self):
        return self._jsequence.next().serializeAsJSON()

    def __getattr__(self, item):
        return getattr(self._jsequence, item)