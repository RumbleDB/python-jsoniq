from jsoniq import RumbleSession
from unittest import TestCase
import json
class TryTesting(TestCase):
    def test1(self):
        # The syntax to start a session is similar to that of Spark.
        # A RumbleSession is a SparkSession that additionally knows about RumbleDB.
        # All attributes and methods of SparkSession are also available on RumbleSession.
        rumble = RumbleSession.builder.appName("PyRumbleExample").getOrCreate();
        # A more complex, standalone query

        seq = rumble.jsoniq("""
        let $stores :=
        [
        { "store number" : 1, "state" : "MA" },
        { "store number" : 2, "state" : "MA" },
          { "store number" : 3, "state" : "CA" },
          { "store number" : 4, "state" : "CA" }
        ]
        let $sales := [
           { "product" : "broiler", "store number" : 1, "quantity" : 20  },
           { "product" : "toaster", "store number" : 2, "quantity" : 100 },
           { "product" : "toaster", "store number" : 2, "quantity" : 50 },
           { "product" : "toaster", "store number" : 3, "quantity" : 50 },
           { "product" : "blender", "store number" : 3, "quantity" : 100 },
           { "product" : "blender", "store number" : 3, "quantity" : 150 },
           { "product" : "socks", "store number" : 1, "quantity" : 500 },
           { "product" : "socks", "store number" : 2, "quantity" : 10 },
           { "product" : "shirt", "store number" : 3, "quantity" : 10 }
        ]
        let $join :=
          for $store in $stores[], $sale in $sales[]
          where $store."store number" = $sale."store number"
          return {
            "nb" : $store."store number",
            "state" : $store.state,
            "sold" : $sale.product
          }
        return [$join]
        """);

        expected = [[{'nb': 1, 'state': 'MA', 'sold': 'broiler'}, {'nb': 1, 'state': 'MA', 'sold': 'socks'}, {'nb': 2, 'state': 'MA', 'sold': 'toaster'}, {'nb': 2, 'state': 'MA', 'sold': 'toaster'}, {'nb': 2, 'state': 'MA', 'sold': 'socks'}, {'nb': 3, 'state': 'CA', 'sold': 'toaster'}, {'nb': 3, 'state': 'CA', 'sold': 'blender'}, {'nb': 3, 'state': 'CA', 'sold': 'blender'}, {'nb': 3, 'state': 'CA', 'sold': 'shirt'}]]

        self.assertTrue(json.dumps(seq.json()) == json.dumps(expected))
