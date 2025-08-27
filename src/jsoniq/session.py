from pyspark.sql import SparkSession
from .sequence import SequenceOfItems
import sys
import platform
import os
import re
import pandas as pd
import importlib.resources as pkg_resources

with pkg_resources.path("jsoniq.jars", "rumbledb-2.0.0.jar") as jar_path:
    jar_path_str = "file://" + str(jar_path)

def get_spark_version():
    if os.environ.get('SPARK_HOME') != None:
        spark_version = os.popen("spark-submit --version 2>&1").read()
        if "version" in spark_version:
            match = re.search(r'version (\d+\.\d+.\d+)', spark_version)
            if match:
                return match.group(1)
    return None

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

    def getRumbleConf(self):
        return self._jrumblesession.getConfiguration()

    class Builder:
        def __init__(self):

            java_version = os.popen("java -version 2>&1").read()
            if "version" in java_version:
                match = re.search(r'version "(\d+\.\d+)', java_version)
                if match:
                    version = match.group(1)
                    if not (version.startswith("17.") or version.startswith("21.")):
                        sys.stderr.write("**************************************************************************\n")
                        sys.stderr.write("[Error] RumbleDB builds on top of pyspark 4, which requires Java 17 or 21.\n")
                        sys.stderr.write(f"Your Java version: {version}\n")
                        sys.stderr.write("**************************************************************************\n")
                        sys.stderr.write("\n")
                        sys.stderr.write("What should you do?\n")
                        sys.stderr.write("\n")
                        sys.stderr.write("If you do NOT have Java 17 or 21 installed, you can download Java 17 or 21 for example from https://adoptium.net/\n")
                        sys.stderr.write("\n")
                        sys.stderr.write("Quick command for macOS: brew install --cask temurin17    or    brew install --cask temurin21\n")
                        sys.stderr.write("Quick command for Ubuntu: apt-get install temurin-17-jdk    or    apt-get install temurin-21-jdk\n")
                        sys.stderr.write("Quick command for Windows 11: winget install EclipseAdoptium.Temurin.17.JDK   or.   winget install EclipseAdoptium.Temurin.21.JDK\n")
                        sys.stderr.write("\n")
                        sys.stderr.write(
                            "If you DO have Java 17 or 21, but the wrong version appears above, then it means you need to set your JAVA_HOME environment variable properly to point to Java 17 or 21.\n"
                        )
                        sys.stderr.write("\n")
                        sys.stderr.write("For macOS, try: export JAVA_HOME=$(/usr/libexec/java_home -v 17)    or    export JAVA_HOME=$(/usr/libexec/java_home -v 21)\n");
                        sys.stderr.write("\n")
                        sys.stderr.write("For Ubuntu, find the paths to installed versions with this command: update-alternatives --config java\n  then: export JAVA_HOME=...your desired path...\n")
                        sys.stderr.write("\n")
                        sys.stderr.write("For Windows 11: look for the default Java path with 'which java' and/or look for alternate installed versions in Program Files. Then: setx /m JAVA_HOME \"...your desired path here...\"\n")
                        sys.exit(43)
            else:
                sys.stderr.write("[Error] Could not determine Java version. Please ensure Java is installed and JAVA_HOME is properly set.\n")
                sys.exit(43)
            self._sparkbuilder = SparkSession.builder.config("spark.jars", jar_path_str)

        def getOrCreate(self):
            if RumbleSession._rumbleSession is None:
                try:
                    RumbleSession._rumbleSession = RumbleSession(self._sparkbuilder.getOrCreate())
                except FileNotFoundError as e:
                    if not os.environ.get('SPARK_HOME') is None:
                        sys.stderr.write("[Error] SPARK_HOME environment variable may not be set properly. Please check that it points to a valid path to a Spark 4.0 directory, or maybe the easiest would be to delete the environment variable SPARK_HOME completely to fall back to the installation of Spark 4.0 packaged with pyspark.\n")
                        sys.stderr.write(f"Current value of SPARK_HOME: {os.environ.get('SPARK_HOME')}\n")
                        sys.exit(43)
                    else:
                        raise e
                except TypeError as e:
                    spark_version = get_spark_version()
                    if not os.environ.get('SPARK_HOME') is None and spark_version is None:
                        sys.stderr.write("[Error] Could not determine Spark version. The SPARK_HOME environment variable may not be set properly. Please check that it points to a valid path to a Spark 4.0 directory, or maybe the easiest would be to delete the environment variable SPARK_HOME completely to fall back to the installation of Spark 4.0 packaged with pyspark.\n")
                        sys.stderr.write(f"Current value of SPARK_HOME: {os.environ.get('SPARK_HOME')}\n")
                        sys.exit(43)
                    elif not os.environ.get('SPARK_HOME') is None and not spark_version.startswith("4.0"):
                        sys.stderr.write(f"[Error] RumbleDB requires Spark 4.0, but found version {spark_version}. Please either set SPARK_HOME to a Spark 4.0 directory, or maybe the easiest would be to delete the environment variable SPARK_HOME completely to fall back to the installation of Spark 4.0 packaged with pyspark.\n")
                        sys.exit(43)
                    else:
                        sys.stderr.write(f"[Error] SPARK_HOME is not set, but somehow pyspark is not falling back to the packaged Spark 4.0.0 version.\n")
                        sys.stderr.write(f"We would appreciate a bug report with some information about your OS, setup, etc.\n")
                        sys.stderr.write(f"In the meantime, what you could do as a workaround is download the Spark 4.0.0 zip file from spark.apache.org, unzip it to some local directory, and point SPARK_HOME to this directory.\n")
                        raise e
            return RumbleSession._rumbleSession
        
        def create(self):
            RumbleSession._rumbleSession = RumbleSession(self._sparkbuilder.create())
            return RumbleSession._rumbleSession

        def remote(self, spark_url):
            self._sparkbuilder = self._sparkbuilder.remote(spark_url)
            return self

        def appName(self, name):
            self._sparkbuilder = self._sparkbuilder.appName(name);
            return self;

        def master(self, url):
            self._sparkbuilder = self._sparkbuilder.master(url);
            return self;
    
        def config(self, key=None, value=None, conf=None, *, map=None):
            self._sparkbuilder = self._sparkbuilder.config(key=key, value=value, conf=conf, map=map)
            return self;

        def withDelta(self):
            self._sparkbuilder = self._sparkbuilder \
                .config("spark.sql.extensions", "io.delta.sql.DeltaSparkSessionExtension") \
                .config("spark.sql.catalog.spark_catalog", "org.apache.spark.sql.delta.catalog.DeltaCatalog") \
                .config("spark.jars.packages", "io.delta:delta-spark_2.13:4.0.0")
            return self;

        def __getattr__(self, name):
            res = getattr(self._sparkbuilder, name);
            return res;

    _builder = Builder()
    _rumbleSession = None

    def convert(self, value):
        if isinstance(value, tuple):
            return [ self.convert(v) for v in value]
        if isinstance(value, bool):
            return self._sparksession._jvm.org.rumbledb.items.ItemFactory.getInstance().createBooleanItem(value)
        elif isinstance(value, str):
            return self._sparksession._jvm.org.rumbledb.items.ItemFactory.getInstance().createStringItem(value)
        elif isinstance(value, int):
            return self._sparksession._jvm.org.rumbledb.items.ItemFactory.getInstance().createLongItem(value)
        elif isinstance(value, float):
            return self._sparksession._jvm.org.rumbledb.items.ItemFactory.getInstance().createDoubleItem(value)
        elif value is None:
            return self._sparksession._jvm.org.rumbledb.items.ItemFactory.getInstance().createNullItem()
        elif isinstance(value, list):
            java_list = self._sparksession._jvm.java.util.ArrayList()
            for v in value:
                java_list.add(self.convert(v))
            return self._sparksession._jvm.org.rumbledb.items.ItemFactory.getInstance().createArrayItem(java_list, False)
        elif isinstance(value, dict):
            java_map = self._sparksession._jvm.java.util.HashMap()
            for k, v in value.items():
                java_list = self._sparksession._jvm.java.util.ArrayList()
                java_list.add(self.convert(v))
                java_map[k] = java_list
            return self._sparksession._jvm.org.rumbledb.items.ItemFactory.getInstance().createObjectItem(java_map, False)
        else:
            raise ValueError("Cannot yet convert value of type " + str(type(value)) + " to a RumbleDB item. Please open an issue and we will look into it!")

    def unbind(self, name: str):
        conf = self._jrumblesession.getConfiguration();
        if not name.startswith("$"):
            raise ValueError("Variable name must start with a dollar symbol ('$').")
        name = name[1:]
        conf.resetExternalVariableValue(name);

    def bind(self, name: str, valueToBind):
        conf = self._jrumblesession.getConfiguration();
        if not name.startswith("$"):
            raise ValueError("Variable name must start with a dollar symbol ('$').")
        name = name[1:]
        if isinstance(valueToBind, SequenceOfItems):
            outputs = valueToBind.availableOutputs()
            if isinstance(outputs, list) and "DataFrame" in outputs:
                conf.setExternalVariableValue(name, valueToBind.df());
            # TODO support binding a variable to an RDD
            #elif isinstance(outputs, list) and "RDD" in outputs:
            #    conf.setExternalVariableValue(name, valueToBind.getAsRDD());
            else:
                conf.setExternalVariableValue(name, valueToBind.items());
        elif isinstance(valueToBind, pd.DataFrame):
            pysparkdf = self._sparksession.createDataFrame(valueToBind)
            conf.setExternalVariableValue(name, pysparkdf._jdf);
        elif isinstance(valueToBind, tuple):
            conf.setExternalVariableValue(name, self.convert(valueToBind))
        elif isinstance(valueToBind, list):
            raise ValueError("""
            To avoid confusion, a sequence of items must be provided as a Python tuple, not as a Python list.
            Lists are mapped to single array items, while tuples are mapped to sequences of items.
            
            If you want to interpret the list as a sequence of items (one item for each list member), then you need to convert it to a tuple.
            Example: [1,2,3] should then be rewritten as tuple([1,2,3]) for the sequence of three (integer) items 1, 2, and 3.

            If you want to interpret the list as a sequence of one array item, then you need to create a singleton tuple.
            Example: [1,2,3] should then be rewritten as ([1,2,3],) for the sequence of one (array) item [1,2,3].
            """)
        elif isinstance(valueToBind, dict):
            conf.setExternalVariableValue(name, self.convert((valueToBind, )))
        elif isinstance(valueToBind, str):
            conf.setExternalVariableValue(name, self.convert((valueToBind, )))
        elif isinstance(valueToBind, int):
            conf.setExternalVariableValue(name, self.convert((valueToBind, )))
        elif isinstance(valueToBind, float):
            conf.setExternalVariableValue(name, self.convert((valueToBind, )))
        elif isinstance(valueToBind, bool):
            conf.setExternalVariableValue(name, self.convert((valueToBind, )))
        elif valueToBind is None:
            conf.setExternalVariableValue(name, self.convert((valueToBind, )))
        elif(hasattr(valueToBind, "_get_object_id")):
            conf.setExternalVariableValue(name, valueToBind);
        else:
            conf.setExternalVariableValue(name, valueToBind._jdf);
        return self;

    def bindOne(self, name: str, value):
        return self.bind(name, (value,))

    def bindDataFrameAsVariable(self, name: str, df):
        conf = self._jrumblesession.getConfiguration();
        if not name.startswith("$"):
            raise ValueError("Variable name must start with a dollar symbol ('$').")
        name = name[1:]
        if(hasattr(df, "_get_object_id")):
            conf.setExternalVariableValue(name, df);
        else:
            conf.setExternalVariableValue(name, df._jdf);
        return self;

    def jsoniq(self, str, **kwargs):
        for key, value in kwargs.items():
            self.bind(f"${key}", value);
        sequence = self._jrumblesession.runQuery(str);
        seq = SequenceOfItems(sequence, self);
        for key, value in kwargs.items():
            self.unbind(f"${key}");
        return seq;

    def __getattr__(self, item):
        return getattr(self._sparksession, item)