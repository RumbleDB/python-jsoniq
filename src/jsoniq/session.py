from pyspark.sql import SparkSession
from .sequence import SequenceOfItems

class MetaRumbleSession(type):
    def __getattr__(cls, item):
        print(f"Dynamically handled: {item}")
        if item == "builder":
            return cls._builder
        else:
            return getattr(SparkSession, item)
    
class RumbleSession(object, metaclass=MetaRumbleSession):
    def __init__(self, spark_session: SparkSession):
        print("Initializing RumbleSession object");
        self._sparksession = spark_session
        self._jrumblesession = spark_session._jvm.org.rumbledb.api.Rumble(spark_session._jsparkSession)

    class Builder:
        def __init__(self):
            self._sparkbuilder = SparkSession.builder.config("spark.jars", "file:///Users/ghislain/Code/rumble/target/rumbledb-1.24.0-jar-with-dependencies.jar")

        def getOrCreate(self):
            print("getOrCreate called");
            return RumbleSession(self._sparkbuilder.getOrCreate())
        
        def appName(self, name):
            print(f"Setting app name: {name}");
            self._sparkbuilder = self._sparkbuilder.appName(name);
            return self;

        def master(self, url):
            print(f"Setting master URL: {url}");
            self._sparkbuilder = self._sparkbuilder.master(url);
            return self;
    
        def config(self, key, value):
            print(f"Setting config: {key} = {value}");
            self._sparkbuilder = self._sparkbuilder.config(key, value);   
            return self;

        def config(self, conf):
            print(f"Setting config: {conf}");
            self._sparkbuilder = self._sparkbuilder.config(conf);   
            return self;

        def __getattr__(self, name):
            print(f"Calling attribute: {name}");
            res = getattr(self._sparkbuilder, name);
            return res;

    _builder = Builder()

    def bindDataFrameAsVariable(self, name: str, df):
        print(f"Binding DataFrame as variable: {name}");
        conf = self._jrumblesession.getConfiguration();
        if not name.startswith("$"):
            raise ValueError("Variable name must start with a dollar symbol ('$').")
        name = name[1:]
        conf.setExternalVariableValue(name, df._jdf);
        return self;

    def jsoniq(self, str):
        sequence = self._jrumblesession.runQuery(str);
        return SequenceOfItems(sequence);

    def __getattr__(self, item):
        print(f"Accessing attribute: {item}")
        return getattr(self._sparksession, item)