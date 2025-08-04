from pyspark.sql import SparkSession
from .sequence import SequenceOfItems
import sys
import platform
import os
import re
import pandas as pd
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
                RumbleSession._rumbleSession = RumbleSession(self._sparkbuilder.getOrCreate())
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
            raise ValueError("To avoid confusion, a sequence of items must be provided as a Python tuple, not as a Python list. Lists are mapped to single array items, while tuples are mapped to sequences of items. If you want to interpret the list as a sequence of items (one item for each list member), then you need to change this list to a tuple by wrapping it into a tuple() call. If you want to bind the variable to one array item, then you need to wrap the provided list inside a singleton tuple and try again, or you can also call bindOne() instead.")
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

    def jsoniq(self, str):
        sequence = self._jrumblesession.runQuery(str);
        return SequenceOfItems(sequence, self);

    def __getattr__(self, item):
        return getattr(self._sparksession, item)