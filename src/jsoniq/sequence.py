from pyspark import RDD
from pyspark.sql import SparkSession
from pyspark.sql import DataFrame
import json
import sys

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
        if (not "DataFrame" in self._jsequence.availableOutputs()):
            sys.stderr.write(self.schema_str)
            return None
        return DataFrame(self._jsequence.getAsDataFrame(), self._sparksession)

    def pdf(self):
        if (not "DataFrame" in self._jsequence.availableOutputs()):
            sys.stderr.write(self.schema_str)
            return None
        return self.df().toPandas()
    
    def count(self):
        return self._jsequence.count()
    
    def nextJSON(self):
        return self._jsequence.next().serializeAsJSON()

    def __getattr__(self, item):
        return getattr(self._jsequence, item)