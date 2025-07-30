from pyspark import RDD
from pyspark.sql import SparkSession
from pyspark.sql import DataFrame
import json

class SequenceOfItems:
    def __init__(self, sequence, rumblesession):
        self._jsequence = sequence
        self._rumblesession = rumblesession
        self._sparksession = rumblesession._sparksession
        self._sparkcontext = self._sparksession.sparkContext

    def items(self):
        return self.getAsList()

    def take(self, n):
        return tuple(self.getFirstItemsAsList(n))
    
    def first(self):
        return tuple(self.getFirstItemsAsList(self._rumblesession.getRumbleConf().getResultSizeCap()))

    def json(self):
        return tuple([json.loads(l.serializeAsJSON()) for l in self._jsequence.getAsList()])

    def rdd(self):
        rdd = self._jsequence.getAsPickledStringRDD()
        rdd = RDD(rdd, self._sparkcontext)
        return rdd.map(lambda l: json.loads(l))

    def df(self):
        return DataFrame(self._jsequence.getAsDataFrame(), self._sparksession)

    def pdf(self):
        return self.df().toPandas()
    
    def count(self):
        return self._jsequence.count()
    
    def nextJSON(self):
        return self._jsequence.next().serializeAsJSON()

    def __getattr__(self, item):
        return getattr(self._jsequence, item)