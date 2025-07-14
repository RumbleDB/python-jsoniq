# RumbleDB for Python

by Abishek Ramdas and Ghislain Fourny

This is the Python edition of [RumbleDB](https://rumbledb.org/), which brings [JSONiq](https://www.jsoniq.org) to the world of Spark and DataFrames. JSONiq is a language considerably more powerful than SQL as it can process [messy, heterogeneous datasets](https://arxiv.org/abs/1910.11582), from kilobytes to Petabytes, with very little coding effort.

The Python edition of RumbleDB is currently only a prototype (alpha) and probably unstable. We welcome bug reports.

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

Any number of Python DataFrames can be attached to external JSONiq variables used in the query. It will later also be possible to read tables registered in the Hive metastore, similar to spark.sql(). Alternatively, the JSONiq query can also read many files of many different formats from many places (local drive, HTTP, S3, HDFS, ...) directly with simple builtin function calls such as json-lines(), text-file(), parquet-file(), csv-file(), etc. See [RumbleDB's documentation](https://rumble.readthedocs.io/en/latest/).

The resulting sequence of items can be retrieved as DataFrame, as an RDD, as a Python list, or with a streaming iteration over the items.

The individual items can be processed using the RumbleDB [Item API](https://github.com/RumbleDB/rumble/blob/master/src/main/java/org/rumbledb/api/Item.java).

Alternatively, it is possible to directly get a Python list of JSON values, or a streaming iteration of JSON values. This is a convenience that makes it unnecessary to use the Item API, especially for a first-time user.

It is also possible to write the sequence of items to the local disk, to HDFS, to S3, etc in a way similar to how DataFrames are written back by Spark.

The design goal is that it should be possible to chain DataFrames between JSONiq and Spark SQL queries seamlessly. For example, JSONiq can be used to clean up very messy data and turn it into a clean DataFrame, which can then be processed with Spark SQL, spark.ml, etc.

Any feedback or error reports are very welcome.

## Installation

Install with
```
pip install jsoniq
```

## Sample code

We will make more documentation available as we go. In the meantime, you will find a sample code below that should just run
after installing the library.

```
from jsoniq import RumbleSession

# The syntax to start a session is similar to that of Spark.
# A RumbleSession is a SparkSession that additionally knows about RumbleDB.
# All attributes and methods of SparkSession are also available on RumbleSession. 
rumble = RumbleSession.builder.appName("PyRumbleExample").getOrCreate();

# Create a data frame also similar to Spark (but using the rumble object).
data = [("Alice", 30), ("Bob", 25), ("Charlie", 35)];
columns = ["Name", "Age"];
df = rumble.createDataFrame(data, columns);

# This is how to bind a JSONiq variable to a dataframe. You can bind as many variables as you want.
rumble.bindDataFrameAsVariable('$a', df);

# This is how to run a query. This is similar to spark.sql().
# Since variable $a was bound to a DataFrame, it is automatically declared as an external variable
# and can be used in the query. In JSONiq, it is logically a sequence of objects.
res = rumble.jsoniq('$a.Name');

# There are several ways to collect the outputs, depending on the user needs but also
# on the query supplied.
# This returns a list containing one or several of "DataFrame", "RDD", "PUL", "Local"
# If DataFrame is in the list, df() can be invoked.
# If RDD is in the list, rdd() can be invoked.
# If Local is the list, items() or json() can be invokved, as well as the local iterator API.
modes = res.availableOutputs();
for mode in modes:
    print(mode)

###### Parallel access ######

# This returns a regular data frame that can be further processed with spark.sql() or rumble.jsoniq().
df = res.df();
df.show();

##### Local access ######

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

###### Native Python/JSON Access for bypassing the Item API (but losing on the richer JSONiq type system) ######

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

# It is also possible to write the output to a file locally or on a cluster. The API is similar to that of Spark dataframes.
# Note that it creates a directory and stores the (potentially very large) output in a sharded directory.
# RumbleDB was already tested with up to 64 AWS machines and 100s of TBs of data.
# Of course the examples below are so small that it makes more sense to process the results locally with Python,
# but this shows how GBs or TBs of data obtained from JSONiq can be written back to disk.
seq = rumble.jsoniq("$a.Name");
seq.write().mode("overwrite").json("outputjson");
seq.write().mode("overwrite").parquet("outputparquet");

seq = rumble.jsoniq("1+1");
seq.write().mode("overwrite").text("outputtext");

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

```

# Last updates

## Version 0.1.0 alpha 8
- Ability to write back a sequence of items to local disk, HDFS, S3... in various formats (JSON, CSV, Parquet...).
- Automatically declare external variables bound as DataFrames to improve userfriendliness.
- Simplified the function names to make them more intuitive (json(), items(), df(), rdd(), etc).

## Version 0.1.0 alpha 9
Upgrade to Spark 4, which aligns the internal scala versions to 2.13 and should remove some errors. Requires Java 17 or 21.
