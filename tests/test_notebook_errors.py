from unittest.mock import Mock

import pytest
from py4j.protocol import Py4JJavaError

from jsoniq import RumbleError, RumbleSession
from jsoniq.sequence import SequenceOfItems


def setup_error(debug=False):
    java = Mock()
    java._target_id = "o1"
    java.getMessage.return_value = "Code: [RBST0004]\nMessage: Cannot convert to DataFrame."
    error = Py4JJavaError("Java call failed", java)
    session = Mock()
    session.getRumbleConf.return_value.getBoolean.return_value = debug
    return session, error


@pytest.mark.parametrize("method", ["df", "pdf", "json", "rdd", "count", "nextJSON", "serialize"])
def test_result_errors_are_concise_and_catchable(method):
    session, error = setup_error()
    java_sequence = Mock()
    for name in ["getAsDataFrame", "getAsList", "getAsPickledStringRDD", "count", "next", "serialize"]:
        getattr(java_sequence, name).side_effect = error
    sequence = SequenceOfItems(java_sequence, session)
    with pytest.raises(RumbleError) as caught:
        getattr(sequence, method)()
    assert isinstance(caught.value, Py4JJavaError)
    assert caught.value.java_exception is error.java_exception
    assert caught.value.__cause__ is error
    assert str(caught.value) == error.java_exception.getMessage()
    assert caught.value._render_traceback_() == str(caught.value).splitlines()


def test_debug_preserves_original_exception():
    session, error = setup_error(debug=True)
    java_sequence = Mock()
    java_sequence.getAsDataFrame.side_effect = error
    with pytest.raises(Py4JJavaError) as caught:
        SequenceOfItems(java_sequence, session).pdf()
    assert caught.value is error


@pytest.mark.parametrize("language", ["jsoniq", "xquery"])
def test_query_creation_errors(language):
    session, error = setup_error()
    session._run_query.side_effect = error
    with pytest.raises(RumbleError):
        getattr(RumbleSession, language)(session, "invalid query")


def test_ipython_renders_only_java_message():
    ipython = pytest.importorskip("IPython.core.interactiveshell")
    _, error = setup_error()
    shell = ipython.InteractiveShell()
    output = []
    shell._showtraceback = lambda exception_type, value, traceback: output.extend(traceback)
    try:
        raise RumbleError(error) from error
    except RumbleError:
        shell.showtraceback()
    assert output == error.java_exception.getMessage().splitlines()


def test_non_java_errors_are_unchanged():
    session, _ = setup_error()
    java_sequence = Mock()
    java_sequence.getAsDataFrame.side_effect = ValueError("Python failure")
    with pytest.raises(ValueError, match="Python failure"):
        SequenceOfItems(java_sequence, session).df()
