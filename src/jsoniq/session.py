from pyspark.sql import SparkSession
from py4j.java_collections import JavaList
from .sequence import SequenceOfItems
from .configuration import RumbleConfiguration
import sys
import platform
import os
import re
from threading import RLock
import pandas as pd
from importlib.resources import files, as_file

_spark_creation_lock = RLock()

with as_file(files("jsoniq.jars").joinpath("rumbledb-3.0.0.jar")) as jar_path:
    if (os.name == 'nt'):
        jar_path_str = str(jar_path)
    else:
        jar_path_str = "file://" + str(jar_path)
    print(f"[Info] Using RumbleDB jar file at: {jar_path_str}")

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
        self._configuration = RumbleConfiguration(self)
        self._bindings = {}

    def getRumbleConf(self):
        return self._configuration

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
            self._use_bundled_spark = True
            self._appendable_keys = {
                "spark.jars.packages",
                "spark.sql.extensions",
            }

        def withBundledSpark(self, enabled=True):
            """Use PySpark's bundled Spark by default; pass False to respect SPARK_HOME.

            This only affects startup of a new JVM. Existing sessions are reused.
            """
            self._use_bundled_spark = enabled
            return self

        def _create_session(self, method):
            # Serialize this library's startup calls while changing the process environment.
            with _spark_creation_lock:
                if not self._use_bundled_spark:
                    return RumbleSession(getattr(self._sparkbuilder, method)())
                previous_spark_home = os.environ.pop("SPARK_HOME", None)
                try:
                    return RumbleSession(getattr(self._sparkbuilder, method)())
                finally:
                    if previous_spark_home is None:
                        os.environ.pop("SPARK_HOME", None)
                    else:
                        os.environ["SPARK_HOME"] = previous_spark_home

        def getOrCreate(self):
            if RumbleSession._rumbleSession is None:
                try:
                    RumbleSession._rumbleSession = self._create_session("getOrCreate")
                except FileNotFoundError as e:
                    if not self._use_bundled_spark and not os.environ.get('SPARK_HOME') is None:
                        sys.stderr.write("[Error] SPARK_HOME environment variable may not be set properly. Please check that it points to a valid path to a Spark 4.0 directory, or maybe the easiest would be to delete the environment variable SPARK_HOME completely to fall back to the installation of Spark 4.0 packaged with pyspark.\n")
                        sys.stderr.write(f"Current value of SPARK_HOME: {os.environ.get('SPARK_HOME')}\n")
                        sys.exit(43)
                    else:
                        raise e
                except TypeError as e:
                    if self._use_bundled_spark:
                        raise
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
            RumbleSession._rumbleSession = self._create_session("create")
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

        def _append_config(self, key, value):
            if key not in self._appendable_keys:
                raise ValueError(f"{key} is not an appendable Spark config key.")
            current = self._sparkbuilder._options.get(key)
            if current:
                value = current + "," + value
            self._sparkbuilder = self._sparkbuilder.config(key=key, value=value)
            return self;

        def withDelta(self):
            self._append_config("spark.jars.packages", "io.delta:delta-spark_2.13:4.0.0")
            self._append_config("spark.sql.extensions", "io.delta.sql.DeltaSparkSessionExtension")
            self._sparkbuilder = self._sparkbuilder \
                .config("spark.sql.catalog.spark_catalog", "org.apache.spark.sql.delta.catalog.DeltaCatalog")
            return self;
    
        def withIceberg(self, catalog_names=None):
            """
            Configure Iceberg catalog(s).

            - If no catalogs are provided (None or empty), the session catalog (spark_catalog)
              is configured for Iceberg.
            - If catalogs are provided, table names must be fully qualified with the catalog
              (<catalog>.<namespace>.<table>). No implicit default is applied.
            - Each configured catalog uses its own warehouse directory under
              ./iceberg-warehouse/<catalog>.
            - These are the default settings for the Iceberg catalog, which can be overridden if needed.
            """
            self._append_config("spark.jars.packages", "org.apache.iceberg:iceberg-spark-runtime-4.0_2.13:1.10.0")
            self._append_config("spark.sql.extensions", "org.apache.iceberg.spark.extensions.IcebergSparkSessionExtensions")
            if catalog_names is None:
                catalog_names = []
            if not isinstance(catalog_names, (list, tuple, set)):
                raise ValueError("catalog_names must be a list, tuple, or set of strings.")
            catalog_names = list(catalog_names)
            if len(catalog_names) == 0:
                catalog_names = ["spark_catalog"]
                catalog_class = "org.apache.iceberg.spark.SparkSessionCatalog"
            else:
                catalog_class = "org.apache.iceberg.spark.SparkCatalog"
            for catalog_name in catalog_names:
                if not isinstance(catalog_name, str) or not catalog_name:
                    raise ValueError("catalog_names must contain non-empty strings.")
                warehouse = f"./iceberg-warehouse/{catalog_name}"
                self._sparkbuilder = self._sparkbuilder \
                    .config(f"spark.sql.catalog.{catalog_name}", catalog_class) \
                    .config(f"spark.sql.catalog.{catalog_name}.type", "hadoop") \
                    .config(f"spark.sql.catalog.{catalog_name}.warehouse", warehouse)
            self._sparkbuilder = self._sparkbuilder \
                .config("spark.sql.iceberg.check-ordering", "false")
            return self;

        def withMongo(self):
            self._append_config("spark.jars.packages", "org.mongodb.spark:mongo-spark-connector_2.13:10.5.0")
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
            return self._sparksession._jvm.org.rumbledb.items.ItemFactory.getInstance().createObjectItemFromValueLists(java_map, False)
        else:
            raise ValueError("Cannot yet convert value of type " + str(type(value)) + " to a RumbleDB item. Please open an issue and we will look into it!")

    def unbind(self, name: str):
        if not name.startswith("$"):
            raise ValueError("Variable name must start with a dollar symbol ('$').")
        name = name[1:]
        self._bindings.pop(name, None)

    def bind(self, name: str, valueToBind):
        if not name.startswith("$"):
            raise ValueError("Variable name must start with a dollar symbol ('$').")
        name = name[1:]
        if isinstance(valueToBind, SequenceOfItems):
            outputs = valueToBind.availableOutputs()
            if isinstance(outputs, (list, JavaList)) and "DataFrame" in outputs:
                self._bindings[name] = ("bindDataFrame", valueToBind.df()._jdf)
            else:
                self._bindings[name] = ("bindItems", valueToBind.items())
        elif isinstance(valueToBind, pd.DataFrame):
            pysparkdf = self._sparksession.createDataFrame(valueToBind)
            self._bindings[name] = ("bindDataFrame", pysparkdf._jdf)
        elif isinstance(valueToBind, tuple):
            self._bindings[name] = ("bindItems", self.convert(valueToBind))
        elif isinstance(valueToBind, JavaList):
            self._bindings[name] = ("bindItems", valueToBind)
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
            self._bindings[name] = ("bindItems", self.convert((valueToBind,)))
        elif isinstance(valueToBind, str):
            self._bindings[name] = ("bindItems", self.convert((valueToBind,)))
        elif isinstance(valueToBind, int):
            self._bindings[name] = ("bindItems", self.convert((valueToBind,)))
        elif isinstance(valueToBind, float):
            self._bindings[name] = ("bindItems", self.convert((valueToBind,)))
        elif isinstance(valueToBind, bool):
            self._bindings[name] = ("bindItems", self.convert((valueToBind,)))
        elif valueToBind is None:
            self._bindings[name] = ("bindItems", self.convert((valueToBind,)))
        elif(hasattr(valueToBind, "_get_object_id")):
            self._bindings[name] = ("bindDataFrame", valueToBind)
        else:
            self._bindings[name] = ("bindDataFrame", valueToBind._jdf)
        return self;

    def bindOne(self, name: str, value):
        return self.bind(name, (value,))

    def bindDataFrameAsVariable(self, name: str, df):
        if not name.startswith("$"):
            raise ValueError("Variable name must start with a dollar symbol ('$').")
        name = name[1:]
        if(hasattr(df, "_get_object_id")):
            self._bindings[name] = ("bindDataFrame", df)
        else:
            self._bindings[name] = ("bindDataFrame", df._jdf)
        return self;

    def jsoniq(self, str, **kwargs):
        return self._run_query(str, self._jrumblesession, kwargs)

    def xquery(self, str, **kwargs):
        """Run a query with XQuery 3.1 as the default language."""
        builder = self._jrumblesession.getConfiguration().toBuilder()
        configuration = getattr(builder, "with")("semantics.queryLanguage", "xquery31").build()
        engine = self._sparksession._jvm.org.rumbledb.api.Rumble(configuration)
        return self._run_query(str, engine, kwargs)

    def _run_query(self, query, engine, kwargs):
        previous_bindings = self._bindings.copy()
        try:
            for key, value in kwargs.items():
                self.bind(f"${key}", value)
            bindings = self._sparksession._jvm.org.rumbledb.api.ExternalBindings()
            for name, (method, value) in self._bindings.items():
                getattr(bindings, method)(name, value)
            sequence = engine.runQuery(query, bindings)
            return SequenceOfItems(sequence, self)
        finally:
            self._bindings = previous_bindings

    def __getattr__(self, item):
        return getattr(self._sparksession, item)
