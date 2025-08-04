from IPython.core.magic import Magics, cell_magic, magics_class
import time, json
from jsoniq.session import RumbleSession
from py4j.protocol import Py4JJavaError

@magics_class
class JSONiqMagic(Magics):
    def run(self, line, cell=None, timed=False):
        if cell is None:
            data = line
        else:
            data = cell

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
        end = time.time()
        if(timed):
           print("Response time: %s ms" % (end - start))

        if ("DataFrame" in response.availableOutputs()):
            print(response.pdf())
        elif ("Local" in response.availableOutputs()):
            capplusone = response.take(rumble.getRumbleConf().getResultSizeCap() + 1)
            if len(capplusone) > rumble.getRumbleConf().getResultSizeCap():
                count = response.count()
                print("The query output %s items, which is too many to display. Displaying the first %s items:" % (count, rumble.getRumbleConf().getResultSizeCap()))
            for e in capplusone[:rumble.getRumbleConf().getResultSizeCap()]:
                print(json.dumps(json.loads(e.serializeAsJSON()), indent=2))
        elif ("PUL" in response.availableOutputs()):
            print("The query output a Pending Update List.")
        else:
            print("No output available.")

    @cell_magic
    def jsoniq(self, line, cell=None):
        return self.run(line, cell, False)

    @cell_magic
    def timedjsoniq(self, line, cell=None):
        return self.run(line, cell, True)