class RumbleConfiguration:
    """Session configuration adapter for RumbleDB's immutable Java configuration.

    Changes apply to subsequent queries. Already-created sequences keep the
    configuration with which they were compiled.
    """

    def __init__(self, session):
        self._session = session

    def set(self, path, value):
        configuration = self._session._jrumblesession.getConfiguration()
        builder = configuration.toBuilder()
        configuration = getattr(builder, "with")(path, value).build()
        self._session._jrumblesession = (
            self._session._sparksession._jvm.org.rumbledb.api.Rumble(configuration)
        )
        return self

    # Migration errors for methods declared in the legacy RumbleRuntimeConfiguration.
    # Source: https://rumbledb.org/docs/latest/api/org/rumbledb/config/RumbleRuntimeConfiguration.html
    # Java overloads share a Python method; inherited java.lang.Object methods are not included.

    def applyUpdates(self):
        raise NotImplementedError(
            'applyUpdates() was removed in RumbleDB 3.0.0. '
            'Use rumble.getRumbleConf().getBoolean("runtime.shouldApplyUpdates") instead.'
        )

    def dataFrameExecution(self):
        raise NotImplementedError(
            'dataFrameExecution() was removed in RumbleDB 3.0.0. '
            'Use rumble.getRumbleConf().getBoolean("runtime.useDataFrameExecution") instead.'
        )

    def dateWithTimezone(self):
        raise NotImplementedError(
            'dateWithTimezone() was removed in RumbleDB 3.0.0. '
            'Use rumble.getRumbleConf().getBoolean("semantics.datesWithTimeZone") instead.'
        )

    def doStaticAnalysis(self):
        raise NotImplementedError(
            'doStaticAnalysis() was removed in RumbleDB 3.0.0. '
            'Use rumble.getRumbleConf().getBoolean("analysis.enableStaticTyping") instead.'
        )

    def functionInlining(self):
        raise NotImplementedError(
            'functionInlining() was removed in RumbleDB 3.0.0. '
            'Use rumble.getRumbleConf().getBoolean("optimization.useFunctionInlining") instead.'
        )

    def getAllowedURIPrefixes(self):
        raise NotImplementedError(
            'getAllowedURIPrefixes() was removed in RumbleDB 3.0.0. URI restrictions were removed '
            'along with the server feature in RumbleDB 3.0. Use the Python library to run '
            'RumbleDB in notebooks: from jsoniq import RumbleSession; rumble = '
            'RumbleSession.builder.getOrCreate(); rumble.jsoniq("1 + 1").json().'
        )

    def getDataFrameExecutionModeDetection(self):
        raise NotImplementedError(
            'getDataFrameExecutionModeDetection() was removed in RumbleDB 3.0.0. '
            'Use rumble.getRumbleConf().getBoolean("runtime.detectDataFrameExecutionMode") instead.'
        )

    @staticmethod
    def getDefaultConfiguration():
        raise NotImplementedError(
            'getDefaultConfiguration() was removed in RumbleDB 3.0.0. '
            'Use rumble._sparksession._jvm.org.rumbledb.api.RumbleConfiguration() to create a default Java configuration; this does not change the active session.'
        )

    def getExternalVariableValue(self, name):
        raise NotImplementedError(
            'getExternalVariableValue() was removed in RumbleDB 3.0.0. Bind a sequence with '
            'rumble.bind("$name", tuple(items)); for a single value (including an array), use '
            'rumble.bindOne("$name", value). For a Java List<Item>, use rumble.bind("$name", '
            'java_items). To evaluate a persistent binding, use rumble.jsoniq("$name").items() '
            'for Java items or .json() for Python values; retain the original value if you need '
            'it without evaluation.'
        )

    def getExternalVariableValueReadFromDataFrame(self, name):
        raise NotImplementedError(
            'getExternalVariableValueReadFromDataFrame() was removed in RumbleDB 3.0.0. Use '
            'rumble.bind("$name", dataframe) or rumble.jsoniq(query, name=dataframe) to bind a '
            'DataFrame. Retain the original DataFrame in Python; rumble.jsoniq("$name").df() '
            'evaluates a persistent binding as a DataFrame.'
        )

    def getExternalVariableValueReadFromFile(self, name):
        raise NotImplementedError(
            'getExternalVariableValueReadFromFile() was removed in RumbleDB 3.0.0. '
            'Retain path in Python; configuration no longer stores file-binding paths. '
            'To read and bind a JSON document instead:\n'
            'import json\n'
            'with open(path) as source:\n'
            '    rumble.bindOne("$name", json.load(source))\n'
            'For a text file:\n'
            'with open(path) as source:\n'
            '    rumble.bindOne("$name", source.read())\n'
            'bindOne() preserves a JSON array as one item. '
            'For large JSON Lines files, use rumble.bind("$name", '
            'rumble.jsoniq("json-lines($path)", path=path)); other formats can use their JSONiq '
            'input function or a Spark DataFrame.'
        )

    def getExternalVariablesReadFromDataFrames(self):
        raise NotImplementedError(
            'getExternalVariablesReadFromDataFrames() was removed in RumbleDB 3.0.0. Bind a '
            'DataFrame with rumble.bind("$name", dataframe), or use rumble.jsoniq(query, '
            'name=dataframe) for one query. There is no public replacement for listing binding '
            'names; keep those names in your Python application.'
        )

    def getExternalVariablesReadFromListsOfItems(self):
        raise NotImplementedError(
            'getExternalVariablesReadFromListsOfItems() was removed in RumbleDB 3.0.0. Bind a '
            'sequence of Python items with rumble.bind("$name", tuple(items)), or use '
            'rumble.jsoniq(query, name=tuple(items)) for one query. For a Java List<Item>, pass '
            'it directly to rumble.bind("$name", java_items). There is no public replacement for '
            'listing binding names; keep those names in your Python application.'
        )

    def getHost(self):
        raise NotImplementedError(
            'getHost() was removed in RumbleDB 3.0.0. The server feature was removed in RumbleDB '
            '3.0. Use the Python library to run RumbleDB in notebooks: from jsoniq import '
            'RumbleSession; rumble = RumbleSession.builder.getOrCreate(); rumble.jsoniq("1 + '
            '1").json().'
        )

    def getInputFormat(self, variableName=None):
        raise NotImplementedError(
            'getInputFormat() was removed in RumbleDB 3.0.0. Neither the global nor the '
            'per-variable format getter has a Python replacement. Keep the selected format '
            'in your Python application; it determines how you parse input before binding. '
            'For JSON from standard input:\n'
            'import json, sys\n'
            'rumble.bindOne("$input", json.load(sys.stdin))\n'
            'For text from standard input:\n'
            'import sys\n'
            'rumble.bindOne("$input", sys.stdin.read())\n'
            'bindOne() preserves a JSON array as one item. Replace "$input" with your '
            'variable name. Input formats now belong to individual engine bindings; the '
            'public Java ExternalBindings API does not expose them yet.'
        )

    def getLaxJSONNullValidation(self):
        raise NotImplementedError(
            'getLaxJSONNullValidation() was removed in RumbleDB 3.0.0. '
            'Use rumble.getRumbleConf().getBoolean("semantics.laxJSONNullValidation") instead.'
        )

    def getLogPath(self):
        raise NotImplementedError(
            'getLogPath() was removed in RumbleDB 3.0.0. '
            'Use rumble.getRumbleConf().getString("output.logPath") instead.'
        )

    def getMaterializationCap(self):
        raise NotImplementedError(
            'getMaterializationCap() was removed in RumbleDB 3.0.0. '
            'Use rumble.getRumbleConf().getInt("runtime.materializationCap") instead.'
        )

    def getNativeSQLPredicates(self):
        raise NotImplementedError(
            'getNativeSQLPredicates() was removed in RumbleDB 3.0.0. '
            'Use rumble.getRumbleConf().getBoolean("runtime.useNativeSQLPredicates") instead.'
        )

    def getNumberOfOutputPartitions(self):
        raise NotImplementedError(
            'getNumberOfOutputPartitions() was removed in RumbleDB 3.0.0. '
            'Use rumble.getRumbleConf().getInt("output.numberOfOutputPartitions") instead.'
        )

    def getOutputPath(self):
        raise NotImplementedError(
            'getOutputPath() was removed in RumbleDB 3.0.0. '
            'Use rumble.getRumbleConf().getString("output.outputPath") instead.'
        )

    def getOverwrite(self):
        raise NotImplementedError(
            'getOverwrite() was removed in RumbleDB 3.0.0. '
            'Use rumble.getRumbleConf().getBoolean("output.allowOverwrite") instead.'
        )

    def getPort(self):
        raise NotImplementedError(
            'getPort() was removed in RumbleDB 3.0.0. The server feature was removed in RumbleDB '
            '3.0. Use the Python library to run RumbleDB in notebooks: from jsoniq import '
            'RumbleSession; rumble = RumbleSession.builder.getOrCreate(); rumble.jsoniq("1 + '
            '1").json().'
        )

    def getQuery(self):
        raise NotImplementedError(
            'getQuery() was removed in RumbleDB 3.0.0. '
            'Use rumble.getRumbleConf().getString("input.query") instead.'
        )

    def getQueryLanguage(self):
        raise NotImplementedError(
            'getQueryLanguage() was removed in RumbleDB 3.0.0. '
            'Use rumble.getRumbleConf().getString("semantics.queryLanguage") instead.'
        )

    def getQueryPath(self):
        raise NotImplementedError(
            'getQueryPath() was removed in RumbleDB 3.0.0. '
            'Use rumble.getRumbleConf().getString("input.queryPath") instead.'
        )

    def getResultSizeCap(self):
        raise NotImplementedError(
            'getResultSizeCap() was removed in RumbleDB 3.0.0. '
            'Use rumble.getRumbleConf().getInt("runtime.resultsSizeCap") instead.'
        )

    def getSerializationParameters(self):
        raise NotImplementedError(
            'getSerializationParameters() was removed in RumbleDB 3.0.0. '
            'Use rumble.getRumbleConf().get("output.serializationParameters") instead. This returns configured parameters as plain Java values, not the former SerializationParameters object.'
        )

    def getShellFilter(self):
        raise NotImplementedError(
            'getShellFilter() was removed in RumbleDB 3.0.0. '
            'Use rumble.getRumbleConf().getString("output.shellFilter") instead.'
        )

    def getShowErrorInfo(self):
        raise NotImplementedError(
            'getShowErrorInfo() was removed in RumbleDB 3.0.0. '
            'Use rumble.getRumbleConf().getBoolean("debug.showErrorInfo") instead.'
        )

    def getStaticBaseUri(self):
        raise NotImplementedError(
            'getStaticBaseUri() was removed in RumbleDB 3.0.0. '
            'Use rumble.getRumbleConf().getString("semantics.staticBaseUri") instead.'
        )

    def getUnparsedExternalVariableValue(self, name):
        raise NotImplementedError(
            'getUnparsedExternalVariableValue() was removed in RumbleDB 3.0.0. Keep the original '
            'text in Python. To bind a string, use rumble.bindOne("$name", text); to parse and '
            'bind a JSON value, use import json; rumble.bindOne("$name", json.loads(text)). These '
            'are distinct operations. For Java lexical bindings, create '
            'org.rumbledb.api.ExternalBindings and call bindLiteral(name, text).'
        )

    def getXmlVersion(self):
        raise NotImplementedError(
            'getXmlVersion() was removed in RumbleDB 3.0.0. '
            'Use rumble.getRumbleConf().getString("semantics.xmlVersion") instead.'
        )

    def init(self):
        raise NotImplementedError(
            'init() was removed in RumbleDB 3.0.0. '
            'No direct replacement is needed: configuration is initialized when the session is created. Use rumble.getRumbleConf().set(path, value) to change a setting.'
        )

    def isCheckReturnTypeOfBuiltinFunctions(self):
        raise NotImplementedError(
            'isCheckReturnTypeOfBuiltinFunctions() was removed in RumbleDB 3.0.0. '
            'Use rumble.getRumbleConf().getBoolean("analysis.checkReturnTypeOfBuiltinFunctions") instead.'
        )

    def isLocal(self):
        raise NotImplementedError(
            'isLocal() was removed in RumbleDB 3.0.0. '
            'Use rumble.sparkContext._jsc.sc().isLocal() instead.'
        )

    def isPrintIteratorTree(self):
        raise NotImplementedError(
            'isPrintIteratorTree() was removed in RumbleDB 3.0.0. '
            'Use rumble.getRumbleConf().getBoolean("debug.printIteratorTree") instead.'
        )

    def isServer(self):
        raise NotImplementedError(
            'isServer() was removed in RumbleDB 3.0.0. The server feature was removed in RumbleDB '
            '3.0. Use the Python library to run RumbleDB in notebooks: from jsoniq import '
            'RumbleSession; rumble = RumbleSession.builder.getOrCreate(); rumble.jsoniq("1 + '
            '1").json().'
        )

    def isShell(self):
        raise NotImplementedError(
            'isShell() was removed in RumbleDB 3.0.0. '
            'Use rumble.getRumbleConf().getString("mode") == "REPL" instead.'
        )

    def nativeExecution(self):
        raise NotImplementedError(
            'nativeExecution() was removed in RumbleDB 3.0.0. '
            'Use rumble.getRumbleConf().getBoolean("runtime.useNativeExecution") instead.'
        )

    def optimizeGeneralComparisonToValueComparison(self):
        raise NotImplementedError(
            'optimizeGeneralComparisonToValueComparison() was removed in RumbleDB 3.0.0. '
            'Use rumble.getRumbleConf().getBoolean("optimization.optimizeGeneralComparisonToValueComparison") instead.'
        )

    def optimizeParentPointers(self):
        raise NotImplementedError(
            'optimizeParentPointers() was removed in RumbleDB 3.0.0. '
            'Use rumble.getRumbleConf().getBoolean("optimization.optimizeParentPointers") instead.'
        )

    def optimizeStepExperimental(self):
        raise NotImplementedError(
            'optimizeStepExperimental() was removed in RumbleDB 3.0.0. '
            'Use rumble.getRumbleConf().getBoolean("optimization.optimizeStepsExperimental") instead.'
        )

    def optimizeSteps(self):
        raise NotImplementedError(
            'optimizeSteps() was removed in RumbleDB 3.0.0. '
            'Use rumble.getRumbleConf().getBoolean("optimization.optimizeSteps") instead.'
        )

    def parallelExecution(self):
        raise NotImplementedError(
            'parallelExecution() was removed in RumbleDB 3.0.0. '
            'Use rumble.getRumbleConf().getBoolean("runtime.useParallelExecution") instead.'
        )

    def printInferredTypes(self):
        raise NotImplementedError(
            'printInferredTypes() was removed in RumbleDB 3.0.0. '
            'Use rumble.getRumbleConf().getBoolean("analysis.printInferredTypes") instead.'
        )

    def read(self, kryo, input):
        raise NotImplementedError(
            'read() was removed in RumbleDB 3.0.0. '
            'No direct replacement: Kryo read/write hooks are not exposed by the public configuration API. Store settings in your application and restore them with rumble.getRumbleConf().set(path, value).'
        )

    def readFromStandardInput(self, variableName):
        raise NotImplementedError(
            'readFromStandardInput() was removed in RumbleDB 3.0.0. This method used to '
            'report whether a variable came from standard input; retain that source '
            'information in Python. To actually read and bind JSON from standard input:\n'
            'import json, sys\n'
            'rumble.bindOne("$input", json.load(sys.stdin))\n'
            'For text from standard input:\n'
            'import sys\n'
            'rumble.bindOne("$input", sys.stdin.read())\n'
            'bindOne() preserves a JSON array as one item. Replace "$input" with your '
            'variable name. The engine has input binding types, including '
            'StandardInputBinding, but the public Java '
            'ExternalBindings API does not expose them yet.'
        )

    def resetExternalVariableValue(self, name):
        raise NotImplementedError(
            'resetExternalVariableValue() was removed in RumbleDB 3.0.0. Use '
            'rumble.unbind("$name") instead, with a dollar-prefixed Python string instead of a '
            'Java Name. Alternatively, use rumble.jsoniq(query, name=value) for a query-scoped '
            'binding that is removed automatically after compilation and restores any previous '
            'persistent binding.'
        )

    def setAllowedURIPrefixes(self, value):
        raise NotImplementedError(
            'setAllowedURIPrefixes() was removed in RumbleDB 3.0.0. URI restrictions were removed '
            'along with the server feature in RumbleDB 3.0. Use the Python library to run '
            'RumbleDB in notebooks: from jsoniq import RumbleSession; rumble = '
            'RumbleSession.builder.getOrCreate(); rumble.jsoniq("1 + 1").json().'
        )

    def setApplyUpdates(self, value):
        raise NotImplementedError(
            'setApplyUpdates() was removed in RumbleDB 3.0.0. '
            f'Use rumble.getRumbleConf().set("runtime.shouldApplyUpdates", {value!r}) instead.'
        )

    def setCheckReturnTypeOfBuiltinFunctions(self, value):
        raise NotImplementedError(
            'setCheckReturnTypeOfBuiltinFunctions() was removed in RumbleDB 3.0.0. '
            f'Use rumble.getRumbleConf().set("analysis.checkReturnTypeOfBuiltinFunctions", {value!r}) instead.'
        )

    def setDataFrameExecution(self, value):
        raise NotImplementedError(
            'setDataFrameExecution() was removed in RumbleDB 3.0.0. '
            f'Use rumble.getRumbleConf().set("runtime.useDataFrameExecution", {value!r}) instead.'
        )

    def setDataFrameExecutionModeDetection(self, value):
        raise NotImplementedError(
            'setDataFrameExecutionModeDetection() was removed in RumbleDB 3.0.0. '
            f'Use rumble.getRumbleConf().set("runtime.detectDataFrameExecutionMode", {value!r}) instead.'
        )

    def setDateWithTimezone(self, value):
        raise NotImplementedError(
            'setDateWithTimezone() was removed in RumbleDB 3.0.0. '
            f'Use rumble.getRumbleConf().set("semantics.datesWithTimeZone", {value!r}) instead.'
        )

    def setExternalVariableValue(self, name, value):
        raise NotImplementedError(
            'setExternalVariableValue() was removed in RumbleDB 3.0.0. Use rumble.bind("$name", '
            'tuple(items)) for a Python sequence, rumble.bindOne("$name", value) for one item '
            '(including an array), or rumble.bind("$name", dataframe) for a DataFrame. A Java '
            'List<Item> can be passed directly as rumble.bind("$name", java_items). For one '
            'query, use rumble.jsoniq(query, name=value), with tuples for sequences and (array,) '
            'for one array item. Replace the Java Name with a dollar-prefixed Python string for '
            'bind()/bindOne(); keyword argument names omit the dollar sign.'
        )

    def setFunctionInlining(self, value):
        raise NotImplementedError(
            'setFunctionInlining() was removed in RumbleDB 3.0.0. '
            f'Use rumble.getRumbleConf().set("optimization.useFunctionInlining", {value!r}) instead.'
        )

    def setInputFormat(self, value):
        raise NotImplementedError(
            'setInputFormat() was removed in RumbleDB 3.0.0. Select the parser in Python '
            'instead of setting a global format. For JSON from standard input:\n'
            'import json, sys\n'
            'rumble.bindOne("$input", json.load(sys.stdin))\n'
            'For text from standard input:\n'
            'import sys\n'
            'rumble.bindOne("$input", sys.stdin.read())\n'
            'For a file, open it with a with statement and pass the file object to '
            'json.load(source) or source.read() instead of sys.stdin. bindOne() preserves '
            'a JSON array as one item. The engine has FileBinding and StandardInputBinding '
            'with InputFormat.JSON or InputFormat.TEXT, but the public Java ExternalBindings '
            'API does not expose them yet. For CLI context-item input, use '
            '--context-item-input - --context-item-input-format json (or text).'
        )

    def setLaxJSONNullValidation(self, value):
        raise NotImplementedError(
            'setLaxJSONNullValidation() was removed in RumbleDB 3.0.0. '
            f'Use rumble.getRumbleConf().set("semantics.laxJSONNullValidation", {value!r}) instead.'
        )

    def setLogPath(self, value):
        raise NotImplementedError(
            'setLogPath() was removed in RumbleDB 3.0.0. '
            f'Use rumble.getRumbleConf().set("output.logPath", {value!r}) instead.'
        )

    def setMaterializationCap(self, value):
        raise NotImplementedError(
            'setMaterializationCap() was removed in RumbleDB 3.0.0. '
            f'Use rumble.getRumbleConf().set("runtime.materializationCap", {value!r}) instead.'
        )

    def setNativeExecution(self, value):
        raise NotImplementedError(
            'setNativeExecution() was removed in RumbleDB 3.0.0. '
            f'Use rumble.getRumbleConf().set("runtime.useNativeExecution", {value!r}) instead.'
        )

    def setNativeSQLPredicates(self, value):
        raise NotImplementedError(
            'setNativeSQLPredicates() was removed in RumbleDB 3.0.0. '
            f'Use rumble.getRumbleConf().set("runtime.useNativeSQLPredicates", {value!r}) instead.'
        )

    def setNumberOfOutputPartitions(self, value):
        raise NotImplementedError(
            'setNumberOfOutputPartitions() was removed in RumbleDB 3.0.0. '
            f'Use rumble.getRumbleConf().set("output.numberOfOutputPartitions", {value!r}) instead.'
        )

    def setOptimizeGeneralComparisonToValueComparison(self, value):
        raise NotImplementedError(
            'setOptimizeGeneralComparisonToValueComparison() was removed in RumbleDB 3.0.0. '
            f'Use rumble.getRumbleConf().set("optimization.optimizeGeneralComparisonToValueComparison", {value!r}) instead.'
        )

    def setOptimizeParentPointers(self, value):
        raise NotImplementedError(
            'setOptimizeParentPointers() was removed in RumbleDB 3.0.0. '
            f'Use rumble.getRumbleConf().set("optimization.optimizeParentPointers", {value!r}) instead.'
        )

    def setOptimizeSteps(self, value):
        raise NotImplementedError(
            'setOptimizeSteps() was removed in RumbleDB 3.0.0. '
            f'Use rumble.getRumbleConf().set("optimization.optimizeSteps", {value!r}) instead.'
        )

    def setOptimizeStepsExperimental(self, value):
        raise NotImplementedError(
            'setOptimizeStepsExperimental() was removed in RumbleDB 3.0.0. '
            f'Use rumble.getRumbleConf().set("optimization.optimizeStepsExperimental", {value!r}) instead.'
        )

    def setOutputPath(self, value):
        raise NotImplementedError(
            'setOutputPath() was removed in RumbleDB 3.0.0. '
            f'Use rumble.getRumbleConf().set("output.outputPath", {value!r}) instead.'
        )

    def setParallelExecution(self, value):
        raise NotImplementedError(
            'setParallelExecution() was removed in RumbleDB 3.0.0. '
            f'Use rumble.getRumbleConf().set("runtime.useParallelExecution", {value!r}) instead.'
        )

    def setPrintIteratorTree(self, value):
        raise NotImplementedError(
            'setPrintIteratorTree() was removed in RumbleDB 3.0.0. '
            f'Use rumble.getRumbleConf().set("debug.printIteratorTree", {value!r}) instead.'
        )

    def setQueryLanguage(self, value):
        raise NotImplementedError(
            'setQueryLanguage() was removed in RumbleDB 3.0.0. '
            f'Use rumble.getRumbleConf().set("semantics.queryLanguage", {value!r}) instead.'
        )

    def setQueryPath(self, value):
        raise NotImplementedError(
            'setQueryPath() was removed in RumbleDB 3.0.0. '
            f'Use rumble.getRumbleConf().set("input.queryPath", {value!r}) instead.'
        )

    def setResultSizeCap(self, value):
        raise NotImplementedError(
            'setResultSizeCap() was removed in RumbleDB 3.0.0. '
            f'Use rumble.getRumbleConf().set("runtime.resultsSizeCap", {value!r}) instead.'
        )

    def setShellFilter(self, value):
        raise NotImplementedError(
            'setShellFilter() was removed in RumbleDB 3.0.0. '
            f'Use rumble.getRumbleConf().set("output.shellFilter", {value!r}) instead.'
        )

    def setShowErrorInfo(self, value):
        raise NotImplementedError(
            'setShowErrorInfo() was removed in RumbleDB 3.0.0. '
            f'Use rumble.getRumbleConf().set("debug.showErrorInfo", {value!r}) instead.'
        )

    def setStaticBaseUri(self, value):
        raise NotImplementedError(
            'setStaticBaseUri() was removed in RumbleDB 3.0.0. '
            f'Use rumble.getRumbleConf().set("semantics.staticBaseUri", {value!r}) instead.'
        )

    def setXmlVersion(self, value):
        raise NotImplementedError(
            'setXmlVersion() was removed in RumbleDB 3.0.0. '
            f'Use rumble.getRumbleConf().set("semantics.xmlVersion", {value!r}) instead.'
        )

    def toString(self):
        raise NotImplementedError(
            'toString() was removed in RumbleDB 3.0.0. '
            'No direct replacement for the old configuration summary. Use rumble.getRumbleConf().get(path) to inspect a section, for example rumble.getRumbleConf().get("runtime").'
        )

    def write(self, kryo, output):
        raise NotImplementedError(
            'write() was removed in RumbleDB 3.0.0. '
            'No direct replacement: Kryo read/write hooks are not exposed by the public configuration API. Read settings with rumble.getRumbleConf().get(path) and serialize those values in your application.'
        )

    def __getattr__(self, name):
        return getattr(self._session._jrumblesession.getConfiguration(), name)
