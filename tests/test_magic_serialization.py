from unittest.mock import Mock, patch

import pytest

pytest.importorskip("IPython")

from jsoniq import RumbleSession
from jsoniqmagic import JSONiqMagic


@pytest.mark.parametrize("option", ["-s", "--serialize", "-s -j", "-s -df", "-s -pdf", "-s -u"])
@pytest.mark.parametrize("serialized", ['<result>hello "world"</result>\nsecond line', ""])
def test_magic_prints_serialized_sequence_directly(option, serialized, capsys):
    session = Mock()
    response = session.jsoniq.return_value
    response.serialize.return_value = serialized

    with patch.object(RumbleSession.Builder, "getOrCreate", return_value=session):
        JSONiqMagic().jsoniq(option, "1 to 3")

    session.jsoniq.assert_called_once_with("1 to 3")
    response.serialize.assert_called_once_with()
    response.take.assert_not_called()
    response.df.assert_not_called()
    response.pdf.assert_not_called()
    response.applyPUL.assert_not_called()
    assert capsys.readouterr().out == serialized + "\n"


def test_magic_reports_serialization_errors(capsys):
    session = Mock()
    session.jsoniq.return_value.serialize.side_effect = RuntimeError("Serialization failed")

    with patch.object(RumbleSession.Builder, "getOrCreate", return_value=session):
        JSONiqMagic().jsoniq("-s", "1 to 3")

    assert "Serialization failed" in capsys.readouterr().out


def test_magic_serialization_preserves_timing(capsys):
    session = Mock()
    session.jsoniq.return_value.serialize.return_value = "hello"

    with patch.object(RumbleSession.Builder, "getOrCreate", return_value=session):
        JSONiqMagic().jsoniq("-s -t", '"hello"')

    output = capsys.readouterr().out
    assert output.startswith("hello\nResponse time: ")
    assert output.endswith(" ms\n")


@pytest.mark.parametrize("option", ["", "-s", "--serialize", "-s -j", "-t"])
def test_xquery_magic_defaults_to_serialization(option, capsys):
    session = Mock()
    response = session.xquery.return_value
    response.serialize.return_value = '<greeting>Hello "world"</greeting>'

    with patch.object(RumbleSession.Builder, "getOrCreate", return_value=session):
        JSONiqMagic().xquery(option, "<greeting>Hello</greeting>")

    session.xquery.assert_called_once_with("<greeting>Hello</greeting>")
    session.jsoniq.assert_not_called()
    response.serialize.assert_called_once_with()
    response.take.assert_not_called()
    output = capsys.readouterr().out
    assert output.startswith('<greeting>Hello "world"</greeting>\n')
    if option == "-t":
        assert "Response time:" in output


@pytest.mark.parametrize("option", ["-j", "-df", "-pdf", "-u"])
def test_xquery_magic_explicit_options_override_default(option, capsys):
    session = Mock()
    response = session.xquery.return_value
    session.getRumbleConf.return_value.getInt.return_value = 10
    item = Mock()
    item.serializeAsJSON.return_value = "42"
    response.take.return_value = [item]
    response.availableOutputs.return_value = ["PUL"]

    with patch.object(RumbleSession.Builder, "getOrCreate", return_value=session):
        result = JSONiqMagic().xquery(option, "42")

    response.serialize.assert_not_called()
    if option == "-j":
        assert capsys.readouterr().out == "42\n"
    elif option == "-df":
        response.df.return_value.show.assert_called_once_with()
        response.take.assert_not_called()
    elif option == "-pdf":
        assert result is response.pdf.return_value
        response.take.assert_not_called()
    else:
        response.applyPUL.assert_called_once_with()
        assert "Updates applied successfully." in capsys.readouterr().out
