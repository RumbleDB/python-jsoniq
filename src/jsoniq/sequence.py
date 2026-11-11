from pyspark import RDD
from pyspark.sql import SparkSession
from pyspark.sql import DataFrame
import json
import sys
from .errors import notebook_errors

class SequenceOfItems:
    schema_str = """
No DataFrame available as no schema was automatically detected. If you still believe the output is structured enough, you could add a schema and validate expression explicitly to your query.

This is an example of how you can simply define a schema and wrap your query in a validate expression:

declare type local:mytype as {
    "product" : "string",
    "store-number" : "int",
    "quantity" : "decimal"
};
validate type local:mytype* { 
    for $product in json-lines("http://rumbledb.org/samples/products-small.json", 10)
    where $product.quantity ge 995
    return $product
}

RumbleDB keeps getting improved and automatic schema detection will improve as new versions get released. But even when RumbleDB fails to detect a schema, you can always declare your own schema as shown above.

For more information, see the documentation at https://docs.rumbledb.org/rumbledb-reference/types
"""

    def __init__(self, sequence, rumblesession):
        self._jsequence = sequence
        self._rumblesession = rumblesession
        self._sparksession = rumblesession._sparksession
        self._sparkcontext = self._sparksession.sparkContext

    @notebook_errors
    def items(self):
        return self.getAsList()

    @notebook_errors
    def take(self, n):
        self._rumblesession.lastResult =  tuple(self.getFirstItemsAsList(n))
        return self._rumblesession.lastResult
    
    @notebook_errors
    def first(self):
        self._rumblesession.lastResult =  tuple(self.getFirstItemsAsList(self._rumblesession.getRumbleConf().getInt("runtime.resultsSizeCap")))
        return self._rumblesession.lastResult

    @notebook_errors
    def json(self):
        self._rumblesession.lastResult = tuple([json.loads(l.serializeAsJSON()) for l in self._jsequence.getAsList()])
        return self._rumblesession.lastResult

    @notebook_errors
    def rdd(self):
        rdd = self._jsequence.getAsPickledStringRDD()
        rdd = RDD(rdd, self._sparkcontext)
        self._rumblesession.lastResult = rdd.map(lambda l: json.loads(l))
        return self._rumblesession.lastResult

    @notebook_errors
    def df(self):
        self._rumblesession.lastResult = DataFrame(self._jsequence.getAsDataFrame(), self._sparksession)
        return self._rumblesession.lastResult

    @notebook_errors
    def pdf(self):
        self._rumblesession.lastResult = self.df().toPandas()
        return self._rumblesession.lastResult
    
    @notebook_errors
    def count(self):
        return self._jsequence.count()
    
    @notebook_errors
    def nextJSON(self):
        return self._jsequence.next().serializeAsJSON()

    def __getattr__(self, item):
        value = getattr(self._jsequence, item)
        if callable(value):
            @notebook_errors
            def call(sequence, *args, **kwargs):
                return value(*args, **kwargs)
            return call.__get__(self, type(self))
        return value
