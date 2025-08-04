from jsoniq import RumbleSession
from unittest import TestCase
import json
import pandas as pd

class TryTesting(TestCase):
    def test1(self):

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
        
        rumble.bind('$c', (1,2,3,4, 5, 6))
        print(rumble.jsoniq("""
        for $v in $c
        let $parity := $v mod 2
        group by $parity
        return { switch($parity)
                case 0 return "even"
                case 1 return "odd"
                default return "?" : $v
        }
        """).json())

        rumble.bind('$c', ([1,2,3],[4,5,6]))
        print(rumble.jsoniq("""
        for $i in $c
        return [
          for $j in $i
          return { "foo" : $j }
        ]
        """).json())

        rumble.bind('$c', ({"foo":[1,2,3]},{"foo":[4,{"bar":[1,False, None]},6]}))
        print(rumble.jsoniq('{ "results" : $c.foo[[2]] }').json())

        # It is possible to bind only one value. The it must be provided as a singleton tuple.
        # This is because in JSONiq, an item is the same a sequence of one item.
        rumble.bind('$c', (42,))
        print(rumble.jsoniq('for $i in 1 to $c return $i*$i').json())

        # For convenience and code readability, you can also use bindOne().
        rumble.bindOne('$c', 42)
        print(rumble.jsoniq('for $i in 1 to $c return $i*$i').json())

        ##########################################################
        ##### Binding JSONiq variables to pandas DataFrames ######
        ##### Getting the output as a Pandas DataFrame      ######
        ##########################################################

        # Creating a dummy pandas dataframe
        data = {'Name': ['Alice', 'Bob', 'Charlie'],
                'Age': [30,25,35]};
        pdf = pd.DataFrame(data);

        # Binding a pandas dataframe
        rumble.bind('$a',pdf);
        seq = rumble.jsoniq('$a.Name')
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

        # This is how to bind a JSONiq variable to a dataframe. You can bind as many variables as you want.
        rumble.bind('$a', df);

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
        rumble.bind('$b', df2);
        seq2 = rumble.jsoniq("for $i in 1 to 5 return $b");
        df3 = seq2.df();
        df3.show();

        # And a DataFrame output by JSONiq can be reused as input to another JSONiq query.
        rumble.bind('$b', df3);
        seq3 = rumble.jsoniq("$b[position() lt 3]");
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
        seq = rumble.jsoniq("$a.Name");
        seq.write().mode("overwrite").json("outputjson");
        seq.write().mode("overwrite").parquet("outputparquet");

        seq = rumble.jsoniq("1+1");
        seq.write().mode("overwrite").text("outputtext");

        self.assertTrue(True)
