# RumbleDB for Python

by Abishek Ramdas and Ghislain Fourny

This is the Python edition of [RumbleDB](https://rumbledb.org/), which brings [JSONiq](https://www.jsoniq.org) to the world of Python.

JSONiq is a language considerably more powerful than SQL as it can process [messy, heterogeneous datasets](https://arxiv.org/abs/1910.11582), from kilobytes to Petabytes, with very little coding effort.

Spark aficionados can also pass DataFrames to JSONiq queries and take back DataFrames. This gives them an environment in which both Spark SQL and JSONiq co-exist to manipulate the data. 

The Python edition of RumbleDB is currently a prototype (alpha) and probably unstable. We welcome bug reports and feedback.

## About RumbleDB

RumbleDB is a JSONiq engine that works both with very small amounts of data and very large amounts of data.
It works with JSON, CSV, text, Parquet, etc (and soon XML).
It works on your laptop as well as on any Spark cluster (AWS, company clusters, etc).

It automatically detects and switches between execution modes in a way transparent to the user, bringing the convenience of data independence to the world of messy data.

It is an academic project, natively in Java, carried out at ETH Zurich by many students over more than 8 years: Stefan Irimescu, Renato Marroquin, Rodrigo Bruno, Falko Noé, Ioana Stefan, Andrea Rinaldi, Stevan Mihajlovic, Mario Arduini, Can Berker Çıkış, Elwin Stephan, David Dao, Zirun Wang, Ingo Müller, Dan-Ovidiu Graur, Thomas Zhou, Olivier Goerens, Alexandru Meterez, Pierre Motard, Remo Röthlisberger, Dominik Bruggisser, David Loughlin, David Buzatu, Marco Schöb, Maciej Byczko, Matteo Agnoletto, Dwij Dixit.

It is free and open source, under an Apache 2.0 license, which can also be used commercially (but on an as-is basis with no guarantee).

## High-level information on the library

A RumbleSession is a wrapper around a SparkSession that additionally makes sure the RumbleDB environment is in scope.

JSONiq queries are invoked with rumble.jsoniq() in a way similar to the way Spark SQL queries are invoked with spark.sql().

JSONiq variables can be bound to lists of JSON values (str, int, float, True, False, None, dict, list) or to Pyspark DataFrames. A JSONiq query can use as many variables as needed (for example, it can join between different collections).

It will later also be possible to read tables registered in the Hive metastore, similar to spark.sql(). Alternatively, the JSONiq query can also read many files of many different formats from many places (local drive, HTTP, S3, HDFS, ...) directly with simple builtin function calls such as json-lines(), text-file(), parquet-file(), csv-file(), etc. See [RumbleDB's documentation](https://docs.rumbledb.org/writing-jsoniq-queries-in-python).

The resulting sequence of items can be retrieved as a list of JSON values, as a Pyspark DataFrame, or, for advanced users, as an RDD or with a streaming iteration over the items using the [RumbleDB Item API](https://github.com/RumbleDB/rumble/blob/master/src/main/java/org/rumbledb/api/Item.java).

It is also possible to write the sequence of items to the local disk, to HDFS, to S3, etc in a way similar to how DataFrames are written back by Pyspark.

The library also contains a jsoniq magic that allows you to directly write JSONiq queries in a Jupyter notebook and see the results automatically output on the screen.

The design goal is that it is possible to chain DataFrames between JSONiq and Spark SQL queries seamlessly. For example, JSONiq can be used to clean up very messy data and turn it into a clean DataFrame, which can then be processed with Spark SQL, spark.ml, etc.

Any feedback or error reports are very welcome.

## Type mapping

Any expression in JSONiq returns a sequence of items. Any variable in JSONiq is bound to a sequence of items.
Items can be objects, arrays, or atomic values (strings, integers, booleans, nulls, dates, binary, durations, doubles, decimal numbers, etc).
A sequence of items can be a sequence of just one item, but it can also be empty, or it can be as large as to contain millions, billions or even trillions of items. Obviously, for sequence longer than a billion items, it is a better idea to use a cluster than a laptop.
A relational table (or more generally a data frame) corresponds to a sequence of object items sharing the same schema. However, sequences of items are more general than tables or data frames and support heterogeneity seamlessly.

When passing Python values to JSONiq or getting them from a JSONiq queries, the mapping to and from Python is as follows: 

| Python | JSONiq |
|-------|-------|
|tuple|sequence of items|
|dict|object|
|list|array|
|str|string|
|int|integer|
|bool|boolean|
|None|null|

Furthermore, other JSONiq types will be mapped to string literals. Users who want to preserve JSONiq types can use the Item API instead.

## Installation

Install with
```
pip install jsoniq
```

*Important note*: since the jsoniq package depends on pyspark 4, Java 17 or Java 21 is a requirement. If another version of Java is installed, the execution of a Python program attempting to create a RumbleSession will lead to an error message on stderr that contains explanations.

## Sample code

We will make more documentation available as we go. In the meantime, you will find a sample, commented code below that should just run
after installing the library.

You can directly copy paste the code below to a Python file and execute it with Python.

```
from jsoniq import RumbleSession
import pandas as pd

# The syntax to start a session is similar to that of Spark.
# A RumbleSession is a SparkSession that additionally knows about RumbleDB.
# All attributes and methods of SparkSession are also available on RumbleSession. 

rumble = RumbleSession.builder.getOrCreate();

# Just to improve readability when invoking Spark methods
# (such as spark.sql() or spark.createDataFrame()).
spark = rumble

##############################
###### Your first query ######
##############################

# Even though RumbleDB uses Spark internally, it can be used without any knowledge of Spark.

# Executing a query is done with rumble.jsoniq() like so. A query returns a sequence
# of items, here the sequence with just the integer item 2.
items = rumble.jsoniq('1+1')

# A sequence of items can simply be converted to a list of Python/JSON values with json().
# Since there is only one value in the sequence output by this query,
# we get a singleton list with the integer 2.
# Generally though, the results may contain zero, one, two, or more items.
python_list = items.json()
print(python_list)

############################################
##### More complex, standalone queries #####
############################################

# JSONiq is very powerful and expressive. You will find tutorials as well as a reference on JSONiq.org.

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

print(seq.json());

seq = rumble.jsoniq("""
for $product in json-lines("http://rumbledb.org/samples/products-small.json", 10)
group by $store-number := $product.store-number
order by $store-number ascending
return {
    "store" : $store-number,
    "products" : [ distinct-values($product.product) ]
}
""");
print(seq.json());

############################################################
###### Binding JSONiq variables to Python values ###########
############################################################

# It is possible to bind a JSONiq variable to a tuple of native Python values
# and then use it in a query.
# JSONiq, variables are bound to sequences of items, just like the results of JSONiq
# queries are sequence of items.
# A Python tuple will be seamlessly converted to a sequence of items by the library.
# Currently we only support strs, ints, floats, booleans, None, lists, and dicts.
# But if you need more (like date, bytes, etc) we will add them without any problem.
# JSONiq has a rich type system.
 
print(rumble.jsoniq("""
for $v in $c
let $parity := $v mod 2
group by $parity
return { switch($parity)
         case 0 return "even"
         case 1 return "odd"
         default return "?" : $v
}
""", c=(1,2,3,4, 5, 6)).json())

print(rumble.jsoniq("""
for $i in $c
return [
  for $j in $i
  return { "foo" : $j }
]
""", c=([1,2,3],[4,5,6])).json())

print(rumble.jsoniq('{ "results" : $c.foo[[2]] }', c=({"foo":[1,2,3]},{"foo":[4,{"bar":[1,False, None]},6]})).json())

# It is possible to bind only one value. The it must be provided as a singleton tuple.
# This is because in JSONiq, an item is the same a sequence of one item.
print(rumble.jsoniq('for $i in 1 to $c return $i*$i', c=(42,)).json())

# For convenience and code readability, you can also use bindOne().
print(rumble.jsoniq('for $i in 1 to $c return $i*$i', c=42).json())

##########################################################
##### Binding JSONiq variables to pandas DataFrames ######
##### Getting the output as a Pandas DataFrame      ######
##########################################################

# Creating a dummy pandas dataframe
data = {'Name': ['Alice', 'Bob', 'Charlie'],
        'Age': [30,25,35]};
pdf = pd.DataFrame(data);

# Binding a pandas dataframe
seq = rumble.jsoniq('$a.Name', a=pdf)
# Getting the output as a pandas dataframe
print(seq.pdf())


################################################
##### Using Pyspark DataFrames with JSONiq #####
################################################

# The power users can also interface our library with pyspark DataFrames.
# JSONiq sequences of items can have billions of items, and our library supports this
# out of the box: it can also run on clusters on AWS Elastic MapReduce for example.
# But your laptop is just fine, too: it will spread the computations on your cores.
# You can bind a DataFrame to a JSONiq variable. JSONiq will recognize this
# DataFrame as a sequence of object items.

# Create a data frame also similar to Spark (but using the rumble object).
data = [("Alice", 30), ("Bob", 25), ("Charlie", 35)];
columns = ["Name", "Age"];
df = spark.createDataFrame(data, columns);

# You can bind JSONiq variables to pyspark DataFrames as follows. You can bind as many variables as you want.
# Since variable $a is bound to a DataFrame, it is automatically declared as an external variable
# and can be used in the query. In JSONiq, it is logically a sequence of objects.
res = rumble.jsoniq('$a.Name', a=df);

# There are several ways to collect the outputs, depending on the user needs but also
# on the query supplied.
# This returns a list containing one or several of "DataFrame", "RDD", "PUL", "Local"
# If DataFrame is in the list, df() can be invoked.
# If RDD is in the list, rdd() can be invoked.
# If Local is the list, items() or json() can be invokved, as well as the local iterator API.
modes = res.availableOutputs();
for mode in modes:
    print(mode)

#########################################################
###### Manipulating DataFrames with SQL and JSONiq ######
#########################################################

# If the output of the JSONiq query is structured (i.e., RumbleDB was able to detect a schema),
# then we can extract a regular data frame that can be further processed with spark.sql() or rumble.jsoniq().
df = res.df();
df.show();

# We are continuously working on the detection of schemas and RumbleDB will get better at it with them.
# JSONiq is a very powerful language and can also produce heterogeneous output "by design". Then you need
# to use rdd() instead of df(), or to collect the list of JSON values (see further down). Remember
# that availableOutputs() tells you what is at your disposal.

# A DataFrame output by JSONiq can be reused as input to a Spark SQL query.
# (Remember that rumble is a wrapper around a SparkSession object, so you can use rumble.sql() just like spark.sql())
df.createTempView("myview")
df2 = spark.sql("SELECT * FROM myview").toDF("name");
df2.show();

# A DataFrame output by Spark SQL can be reused as input to a JSONiq query.
seq2 = rumble.jsoniq("for $i in 1 to 5 return $b", b=df2);
df3 = seq2.df();
df3.show();

# And a DataFrame output by JSONiq can be reused as input to another JSONiq query.
seq3 = rumble.jsoniq("$b[position() lt 3]", b=df3);
df4 = seq3.df();
df4.show();

#########################
##### Local access ######
#########################

# This materializes the rows as items.
# The items are accessed with the RumbleDB Item API.
list = res.items();
for result in list:
    print(result.getStringValue())

# This streams through the items one by one
res.open();
while (res.hasNext()):
    print(res.next().getStringValue());
res.close();

################################################################################################################
###### Native Python/JSON Access for bypassing the Item API (but losing on the richer JSONiq type system) ######
################################################################################################################

# This method directly gets the result as JSON (dict, list, strings, ints, etc).
jlist = res.json();
for str in jlist:
    print(str);

# This streams through the JSON values one by one.
res.open();
while(res.hasNext()):
    print(res.nextJSON());
res.close();

# This gets an RDD of JSON values that can be processed by Python
rdd = res.rdd();
print(rdd.count());
for str in rdd.take(10):
    print(str);

###################################################
###### Write back to the disk (or data lake) ######
###################################################

# It is also possible to write the output to a file locally or on a cluster. The API is similar to that of Spark dataframes.
# Note that it creates a directory and stores the (potentially very large) output in a sharded directory.
# RumbleDB was already tested with up to 64 AWS machines and 100s of TBs of data.
# Of course the examples below are so small that it makes more sense to process the results locally with Python,
# but this shows how GBs or TBs of data obtained from JSONiq can be written back to disk.
seq = rumble.jsoniq("$a.Name", a=spark.createDataFrame(data, columns));
seq.write().mode("overwrite").json("outputjson");
seq.write().mode("overwrite").parquet("outputparquet");

seq = rumble.jsoniq("1+1");
seq.write().mode("overwrite").text("outputtext");

```
# How to learn JSONiq, and more query examples

Even more queries can be found [here](https://colab.research.google.com/github/RumbleDB/rumble/blob/master/RumbleSandbox.ipynb) and you can look at the [JSONiq documentation](https://www.jsoniq.org) and tutorials.

# Latest updates

## Version 2.0.1
- Update to Spark 4.0.1.
- Add postgreSQL connection (postgresql-table()).

## Version 2.0.0
- Aligned on the brand new RumbleDB 2.0 release.
- Improved display of pandas dataframes output with -pdf in Jupyter notebooks.
- if error info is activated in the configuration, then they are now printed in the notebook.
- JSON nulls are now by default conflated with absent upon validating for dataframe output, this can be deactivated in the configuration.
- The materialization error upon df/pdf output is now fixed.

## Version 2.0.0 alpha 1
- When returning a single-column DataFrame with atomic values, the name is now __value and not value to avoid collisions with user-defined columns.
- Improved schema inferrence: DataFrames can be returned in a wider range of cases.
- Improved error display in notebooks when errors happen upon collecting the results and not already upon calling jsoniq().

## Version 0.2.0 alpha 9
- Stability improvements.

## Version 0.2.0 alpha 8
- Variables can now be bound to JSON values, pandas DataFrames or pyspark DataFrames with extra parameters to the rumble.jsoniq() call. It is no longer necessary to explicitly call bind(). This is similar to how DataFrames can be attached to views with extra parameters to spark.sql().
- rumble.lastResult is now correctly assigned also when partial data is returned (only with the partial data).
- Fixed issue with empty array constructors.

## Version 0.2.0 alpha 7
- rumble.lastResult now returns a pyspark/pandas DataFrame or rdd or tuple and no longer the sequence object.
- Enhance schema detection. When the detected static type of the overall query is DataFrame-compatible, it is now automatically possible to obtain the output as a DataFrame without explicitly giving a schema.
- It is now possible to access a table previously registered as a view via a table() function call. This is an alternative to binding variables.
- Enhancements in the JSONiq Update Facility support to update delta files and Hive metastore tables.

## Version 0.2.0 alpha 6
- Fix a bug with the config() call of the builder.
- add withDelta() to configure Delta Lake tables and files, for use with the JSONiq Update Facility.

## Version 0.2.0 alpha 5
- If the initialization of the Spark session fails, we now check if SPARK_HOME is set and if it may be invalid or pointing to a different Spark version than 4.0, and output a more informative error message. 

## Version 0.2.0 alpha 4
- Added parameters to the jsoniq magic to select the desired output to print: -j, -df, -pdf
- Added informative error message with a hint on how to fix when trying to get a DataFrame and there is no schema.
- Added parameter -t to the jsoniq magic to measure the response time
- The RumbleSession object now saves the latest result (sequence of items) in a field called lastResult. This is particularly useful in notebooks for post-processing a result in Python after obtained it through the jsoniq magic.
- Improved static type detection upon binding a pandas or pyspark DataFrame as an input variable to a JSONiq queries.
- Now also accepts pandas version 2.2.

## Version 0.2.0 alpha 2
- You can change the result size cap through to the now accessible Rumble configuration (for example rumble .getRumbleConf().setResultSizeCap(10)). This controls how many items can be retrieved at most with a json() call. You can increase it to whichever number you would like if you reach the cap.
- Add the JSONiq magic to execute JSONiq queries directly in a notebook cell, using the RumbleDB instance shipped with the library.
- RumbleSession.builder.getOrCreate() now correctly reuses an existing session instead of creating a new object. It preserves the configuration. 

## Version 0.2.0 alpha 1
- Allow to bind JSONiq variables to pandas dataframes
- Allow to retrieve the output of a JSONiq query as a pandas dataframe (if the output is available as a dataframe, i.e., availableOutputs() returns a list that contains "DataFrame")
- Clean up the mapping to strictly map tuples to sequence of items, and lists ot array items. This will avoid confusion between arrays and sequences.
- As a consequence, json() now returns a tuple, not a list.
- Calling bind() with a single list will return an informative error. Use bind() with a tuple instead, or call bindOne() to interpret the list as a sequence of one array item.

## Version 0.1.0 alpha 12
- Allow to bind JSONiq variables to Python values (mapping Python lists to sequences of items). This makes it possible to manipulate Python values directly with JSONiq and even without any knowledge of Spark at all.
- renamed bindDataFrameAsVariable() to bind(), which can be used both with DataFrames and Python lists.
- add bindOne() for binding a single value to a JSONiq variable.
- wrapping df() in a Pyspark DataFrame to make sure it can be used with pyspark DataFrame transformations.

## Version 0.1.0 alpha 11
- Fix an issue when feeding a DataFrame output by rumble.jsoniq() back to a new JSONiq query (as a variable).

## Version 0.1.0 alpha 10
- Add an explicit explanation on stderr if the Java version is not properly set, together with hints.

## Version 0.1.0 alpha 9
- Upgrade to Spark 4, which aligns the internal scala versions to 2.13 and should remove some errors. Requires Java 17 or 21.

## Version 0.1.0 alpha 8
- Ability to write back a sequence of items to local disk, HDFS, S3... in various formats (JSON, CSV, Parquet...).
- Automatically declare external variables bound as DataFrames to improve userfriendliness.
- Simplified the function names to make them more intuitive (json(), items(), df(), rdd(), etc).

