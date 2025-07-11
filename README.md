# RumbleDB for Python

by Abishek Ramdas and Ghislain Fourny

This is the Python version of RumbleDB. It is currently only a prototype (alpha) and probably unstable. 

Install with
```
pip install jsoniq
```

Sample code:
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

# There is still a problem to solve to make RDDs work across Python and Java
#rdd = res.getAsJSONRDD();
#print(rdd.count());
#for str in rdd.take(10):
#    print(str);
```
