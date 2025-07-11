from pyspark.sql import SparkSession
from .sequence import SequenceOfItems
import importlib.resources as pkg_resources

with pkg_resources.path("jsoniq.jars", "rumbledb-1.24.0.jar") as jar_path:
    jar_path_str = "file://" + str(jar_path)

class MetaRumbleSession(type):
    def __getattr__(cls, item):
        if item == "builder":
            return cls._builder
        else:
            return getattr(SparkSession, item)
    
class RumbleSession(object, metaclass=MetaRumbleSession):
    def __init__(self, spark_session: SparkSession):
        self._sparksession = spark_session
        self._jrumblesession = spark_session._jvm.org.rumbledb.api.Rumble(spark_session._jsparkSession)

    class Builder:
        def __init__(self):
            self._sparkbuilder = SparkSession.builder.config("spark.jars", jar_path_str)

        def getOrCreate(self):
            return RumbleSession(self._sparkbuilder.getOrCreate())
        
        def appName(self, name):
            self._sparkbuilder = self._sparkbuilder.appName(name);
            return self;

        def master(self, url):
            self._sparkbuilder = self._sparkbuilder.master(url);
            return self;
    
        def config(self, key, value):
            self._sparkbuilder = self._sparkbuilder.config(key, value);   
            return self;

        def config(self, conf):
            self._sparkbuilder = self._sparkbuilder.config(conf);   
            return self;

        def __getattr__(self, name):
            res = getattr(self._sparkbuilder, name);
            return res;

    _builder = Builder()

    def bindDataFrameAsVariable(self, name: str, df):
        conf = self._jrumblesession.getConfiguration();
        if not name.startswith("$"):
            raise ValueError("Variable name must start with a dollar symbol ('$').")
        name = name[1:]
        conf.setExternalVariableValue(name, df._jdf);
        return self;

    def jsoniq(self, str):
        sequence = self._jrumblesession.runQuery(str);
        return SequenceOfItems(sequence, self._sparksession.sparkContext);

    def __getattr__(self, item):
        return getattr(self._sparksession, item)