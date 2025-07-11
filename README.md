# RumbleDB for Python

by Abishek Ramdas and Ghislain Fourny

This is the Python edition of [RumbleDB](https://rumbledb.org/), which brings [JSONiq](https://www.jsoniq.org) to the world of Spark and DataFrames. JSONiq is a language considerably more powerful than SQL as it can process [messy, heterogeneous datasets](https://arxiv.org/abs/1910.11582), from kilobytes to Petabytes, with very little coding effort.

The Python edition of RumbleDB is currently only a prototype (alpha) and probably unstable. 

## High-level information

A RumbleSession is a wrapper around a SparkSession that additionally makes sure the RumbleDB environment is in scope.

JSONiq queries are invoked with rumble.jsoniq() in a way similar to the way Spark SQL queries are invoked with spark.sql().

Any number of Python DataFrames can be attached to JSONiq variables used in the query. It will later also possible to read tables registered in the Hive metastore, similar to spark.sql(). Alternatively, the JSONiq query can also read many files of many different formats from many places (local drive, HTTP, S3, HDFS, ...) directly with simple builtin function calls (see [RumbleDB's documentation](https://rumble.readthedocs.io/en/latest/)).

The resulting sequence of items can be retrieved as DataFrame, as an RDD, as a Python list, or with a streaming iteration over the items.

The individual items can be processed using the RumbleDB [Item API](https://github.com/RumbleDB/rumble/blob/master/src/main/java/org/rumbledb/api/Item.java).

Alternatively, it is possible to directly get an RDD of Python-friendly JSON values, or a Python list of JSON values, or a streaming iteration of JSON values. This is a convenience that makes it unnecessary to use the Item API, especially for a first-time user.

The design goal is that it should be possible to chain DataFrames between JSONiq and Spark SQL queries seamlessly. For example, JSONiq can be used to clean up very messy data and turn it into a clean DataFrame, which can then be processed with Spark SQL, spark.ml, etc.

Any feedback or error reports are very welcome.

## Installation

Install with
```
pip install jsoniq
```

## Sample code

```
from jsoniq import RumbleSession

# The syntax to start a session is similar to Spark.
rumble = RumbleSession.builder.appName("PyRumbleExample").getOrCreate();

# Create a data frame also similar to Spark (but using the rumble object).
data = [("Alice", 30), ("Bob", 25), ("Charlie", 35)];
columns = ["Name", "Age"];
df = rumble.createDataFrame(data, columns);

# This is how to bind a JSONiq variable to a dataframe. You can bind as many variables as you want.
rumble.bindDataFrameAsVariable('$a', df);

# This is how to run a query (declaring the external variable). This is similar to spark.sql().
res = rumble.jsoniq('declare variable $a external; $a.Name');

# returns a list containing one or several of "DataFrame", "RDD", "PUL", "Local"
modes = res.availableOutputs();

###### Parallel access ######

# This returns a regular data frame
df = res.getAsDataFrame();
df.show();

# This returns an RDD containing JSONiq item objects (does not work yet with transformations)
rdd = res.getAsRDD();
print(rdd.count());
for item in rdd.take(10):
    print(item.getStringValue());

##### Local access ######

# This materializes the rows as items.
# The items are access with the RumbleDB Item API.
list = res.getAsList();
for result in list:
    print(result.getStringValue())

# This streams through the items one by one
res.open();
while (res.hasNext()):
    print(res.next().getStringValue());
res.close();

###### Native Python/JSON Access for bypassing the Item API (but losing on the richer JSONiq type system) ######

# This method directly gets the result as JSON (dict, list, strings, ints, etc).
jlist = res.getAsJSONList();
for str in jlist:
    print(str);

# This streams through the JSON values one by one.
res.open();
while(res.hasNext()):
    print(res.nextJSON());
res.close();

# This gets an RDD of JSON values that can be processed by Python                                                                                                                    rdd = res.getAsJSONRDD();
print(rdd.count());
for str in rdd.take(10):
    print(str);
```
