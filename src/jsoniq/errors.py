"""Notebook-friendly Java errors that retain normal exception semantics."""

from functools import wraps

from py4j.protocol import Py4JJavaError


class RumbleError(Py4JJavaError):
    """A Java query error displayed without a traceback by IPython.

    Remains a Py4JJavaError for compatibility with existing exception handlers.
    Ordinary Python execution still reports a traceback.
    """

    def __init__(self, original):
        super().__init__(original.args[0], original.java_exception)
        self.message = original.java_exception.getMessage()

    def __str__(self):
        return self.message or self.java_exception.toString()

    def _render_traceback_(self):
        return str(self).splitlines()


def notebook_errors(method):
    """Translate Java errors unless full debugging output was requested."""
    @wraps(method)
    def wrapped(self, *args, **kwargs):
        try:
            return method(self, *args, **kwargs)
        except RumbleError:
            raise
        except Py4JJavaError as error:
            session = self.__dict__.get("_rumblesession", self)
            if session.getRumbleConf().getBoolean("debug.showErrorInfo"):
                raise
            raise RumbleError(error) from error

    return wrapped
