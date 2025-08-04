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
          max(
            let $path := "http://www.rumbledb.org/samples/git-archive-small.json"
            for $event in json-lines($path)
            return 1
          )
        """);

        expected = [1]

        self.assertTrue(json.dumps(seq.json()) == json.dumps(expected))
