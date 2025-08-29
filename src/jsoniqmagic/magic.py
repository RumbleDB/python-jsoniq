from IPython.core.magic import Magics, cell_magic, magics_class
from IPython.core.magic_arguments import (
    argument, magic_arguments, parse_argstring
)
import time, json
from jsoniq.session import RumbleSession
from py4j.protocol import Py4JJavaError

@magics_class
class JSONiqMagic(Magics):
    @magic_arguments()
    @argument(
        '-t', '--timed', action='store_true', help='Measure execution time.'
    )
    @argument(
        '-df', '--pyspark-data-frame', action='store_true', help='Prints the output as a Pyspark DataFrame (if a schema is available).'
    )
    @argument(
        '-pdf', '--pandas-data-frame', action='store_true', help='Prints the output as a Pandas DataFrame (if a schema is available).'
    )
    @argument(
        '-j', '--json', action='store_true', help='Prints the output as JSON.'
    )
    @argument(
        '-u', '--apply-updates', action='store_true', help='Applies updates if a PUL is output.'
    )
    def run(self, line, cell=None, timed=False):
        if cell is None:
            data = line
        else:
            data = cell

        args = parse_argstring(self.run, line)
        start = time.time()
        try:
            rumble = RumbleSession.builder.getOrCreate();
            response = rumble.jsoniq(data);
        except Py4JJavaError as e:
            print(e.java_exception.getMessage())
            return
        except Exception as e:
            print("Query unsuccessful.")
            print("Usual reasons: firewall, misconfigured proxy.")
            print("Error message:")
            print(e.args[0])
            return
        except:
            print("Query unsuccessful.")
            print("Usual reasons: firewall, misconfigured proxy.")
            return

        schema_str = """
No DataFrame available as no schema was detected. If you still believe the output is structured enough, you could add a schema and validate expression explicitly to your query.

This is an example of how you can simply define a schema and wrap your query in a validate expression:

declare type mytype as {
    "product" : "string",
    "store-number" : "int",
    "quantity" : "decimal"
};
validate type mytype* { 
    for $product in json-lines("http://rumbledb.org/samples/products-small.json", 10)
    where $product.quantity ge 995
    return $product
}
"""

        if(args.pyspark_data_frame):
            try:
                df = response.df();
            except Py4JJavaError as e:
                if rumble.getRumbleConf().getShowErrorInfo() :
                    raise e;
                else:
                    print(e.java_exception.getMessage())
                return
            except Exception as e:
                if rumble.getRumbleConf().getShowErrorInfo() :
                    raise e;
                else:
                    print("Query unsuccessful.")
                    print("Usual reasons: firewall, misconfigured proxy.")
                    print("Error message:")
                    print(e.args[0])
                    return
            except:
                print("Query unsuccessful.")
                print("Usual reasons: firewall, misconfigured proxy.")
                return
            if df is not None:
                df.show()

        if (args.pandas_data_frame):
            try:
                pdf = response.pdf()
            except Py4JJavaError as e:
                if rumble.getRumbleConf().getShowErrorInfo() :
                    raise e;
                else:
                    print(e.java_exception.getMessage())
                return
            except Exception as e:
                print("Query unsuccessful.")
                print("Usual reasons: firewall, misconfigured proxy.")
                print("Error message:")
                print(e.args[0])
                return
            except:
                print("Query unsuccessful.")
                print("Usual reasons: firewall, misconfigured proxy.")
                return
            if pdf is not None:
                return pdf

        if (args.apply_updates):
            if ("PUL" in response.availableOutputs()):
                try:
                    response.applyPUL()
                except Py4JJavaError as e:
                    if rumble.getRumbleConf().getShowErrorInfo() :
                        raise e;
                    else:
                        print(e.java_exception.getMessage())
                    return
                except Exception as e:
                    print("Query unsuccessful.")
                    print("Usual reasons: firewall, misconfigured proxy.")
                    print("Error message:")
                    print(e.args[0])
                    return
                except:
                    print("Query unsuccessful.")
                    print("Usual reasons: firewall, misconfigured proxy.")
                    return  
                print("Updates applied successfully.")
            else:
                print("No Pending Update List (PUL) available to apply.")
        
        if (args.json or (not args.pandas_data_frame and not args.pyspark_data_frame)):
            try:
                capplusone = response.take(rumble.getRumbleConf().getResultSizeCap() + 1)
            except Py4JJavaError as e:
                if rumble.getRumbleConf().getShowErrorInfo() :
                    raise e;
                else:
                    print(e.java_exception.getMessage())
                return
            except Exception as e:
                print("Query unsuccessful.")
                print("Usual reasons: firewall, misconfigured proxy.")
                print("Error message:")
                print(e.args[0])
                return
            except:
                print("Query unsuccessful.")
                print("Usual reasons: firewall, misconfigured proxy.")
                return  
            if len(capplusone) > rumble.getRumbleConf().getResultSizeCap():
                count = response.count()
                print("The query output %s items, which is too many to display. Displaying the first %s items:" % (count, rumble.getRumbleConf().getResultSizeCap()))
            for e in capplusone[:rumble.getRumbleConf().getResultSizeCap()]:
                print(json.dumps(json.loads(e.serializeAsJSON()), indent=2))

        end = time.time()
        if(args.timed):
           print("Response time: %s ms" % (end - start))

    @cell_magic
    def jsoniq(self, line, cell=None):
        return self.run(line, cell, False)
