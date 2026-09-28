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

    def __getattr__(self, name):
        return getattr(self._session._jrumblesession.getConfiguration(), name)
