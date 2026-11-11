from IPython.core.magic import Magics, cell_magic, magics_class
from IPython.core.magic_arguments import (
    argument, magic_arguments, parse_argstring
)
import time, json
from jsoniq.session import RumbleSession
from jsoniq.errors import notebook_error_context

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
        '-s', '--serialize', action='store_true', help='Prints the serialized result sequence without additional quoting.'
    )
    @argument(
        '-u', '--apply-updates', action='store_true', help='Applies updates if a PUL is output.'
    )
    def run(self, line, cell=None, timed=False, language="jsoniq"):
        if cell is None:
            data = line
        else:
            data = cell

        args = parse_argstring(self.run, line)
        if language == "xquery" and not (
            args.json or args.pandas_data_frame or args.pyspark_data_frame or args.apply_updates
        ):
            args.serialize = True
        start = time.time()
        rumble = RumbleSession.builder.getOrCreate();
        with notebook_error_context(rumble):
            return self._execute(rumble, language, data, args, start)

    def _execute(self, rumble, language, data, args, start):
        response = getattr(rumble, language)(data);

        if args.serialize:
            serialized = response.serialize()
            print(serialized)
            if args.timed:
                print("Response time: %s ms" % (time.time() - start))
            return

        if(args.pyspark_data_frame):
            df = response.df();
            if df is not None:
                df.show()

        if (args.pandas_data_frame):
            pdf = response.pdf()
            if pdf is not None:
                return pdf

        if (args.apply_updates):
            if ("PUL" in response.availableOutputs()):
                response.applyPUL()
                print("Updates applied successfully.")
            else:
                print("No Pending Update List (PUL) available to apply.")
        
        if (args.json or (not args.pandas_data_frame and not args.pyspark_data_frame)):
            capplusone = response.take(rumble.getRumbleConf().getInt("runtime.resultsSizeCap") + 1)
            if len(capplusone) > rumble.getRumbleConf().getInt("runtime.resultsSizeCap"):
                count = response.count()
                print("The query output %s items, which is too many to display. Displaying the first %s items:" % (count, rumble.getRumbleConf().getInt("runtime.resultsSizeCap")))
            for e in capplusone[:rumble.getRumbleConf().getInt("runtime.resultsSizeCap")]:
                print(json.dumps(json.loads(e.serializeAsJSON()), indent=2))

        end = time.time()
        if(args.timed):
           print("Response time: %s ms" % (end - start))

    @cell_magic
    def jsoniq(self, line, cell=None):
        return self.run(line, cell, False)

    @cell_magic
    def xquery(self, line, cell=None):
        return self.run(line, cell, False, language="xquery")
