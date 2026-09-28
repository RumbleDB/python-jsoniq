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

    def getResultSizeCap(self):
        return self.getInt("runtime.resultsSizeCap")

    def setResultSizeCap(self, value):
        return self.set("runtime.resultsSizeCap", value)

    def getMaterializationCap(self):
        return self.getInt("runtime.materializationCap")

    def setMaterializationCap(self, value):
        return self.set("runtime.materializationCap", value)

    def getShowErrorInfo(self):
        return self.getBoolean("debug.showErrorInfo")

    def setShowErrorInfo(self, value):
        return self.set("debug.showErrorInfo", value)

    def __getattr__(self, name):
        return getattr(self._session._jrumblesession.getConfiguration(), name)
