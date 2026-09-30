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
