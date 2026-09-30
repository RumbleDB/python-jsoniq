"""Check all documented legacy signatures without starting Spark."""

import json
from pathlib import Path
import runpy

import pytest


ROOT = Path(__file__).resolve().parents[1]
RumbleConfiguration = runpy.run_path(
    str(ROOT / "src/jsoniq/configuration.py")
)["RumbleConfiguration"]
SIGNATURES = json.loads(
    (ROOT / "tests/fixtures/legacy_configuration_methods.json").read_text()
)["signatures"]


@pytest.mark.parametrize("signature", SIGNATURES)
def test_every_documented_signature_raises_migration_error(signature):
    name, parameters = signature[:-1].split("(")
    args = [object() for _ in parameters.split(",")] if parameters else []
    # Any attempt to forward a legacy method to Java would fail on this object.
    configuration = RumbleConfiguration(object())
    assert name in RumbleConfiguration.__dict__
    with pytest.raises(NotImplementedError) as error:
        getattr(configuration, name)(*args)
    assert f"{name}() was removed in RumbleDB 3.0.0." in str(error.value)
    assert len(str(error.value).split("3.0.0. ", 1)[1]) > 0


@pytest.mark.parametrize("name,args", [
    ("getHost", ()), ("getPort", ()), ("isServer", ()),
    ("getAllowedURIPrefixes", ()), ("setAllowedURIPrefixes", (["file:/"],)),
])
def test_server_and_uri_messages_direct_users_to_notebooks(name, args):
    with pytest.raises(NotImplementedError) as error:
        getattr(RumbleConfiguration(object()), name)(*args)
    message = str(error.value)
    assert "removed" in message
    assert "server feature" in message
    assert "Python library" in message
    assert "notebooks" in message


@pytest.mark.parametrize("name,args", [
    ("getInputFormat", ()), ("getInputFormat", ("input",)),
    ("setInputFormat", ("json",)), ("readFromStandardInput", ("input",)),
])
def test_input_messages_preserve_json_arrays_and_explain_api_scope(name, args):
    with pytest.raises(NotImplementedError) as error:
        getattr(RumbleConfiguration(object()), name)(*args)
    message = str(error.value)
    assert 'rumble.bindOne("$input", json.load(sys.stdin))' in message
    assert 'rumble.bindOne("$input", sys.stdin.read())' in message
    assert "does not expose them yet" in message


@pytest.mark.parametrize("name,value,command", [
    ("setResultSizeCap", 42, 'set("runtime.resultsSizeCap", 42)'),
    ("setShowErrorInfo", True, 'set("debug.showErrorInfo", True)'),
    ("setQueryPath", 'a"b.jq', 'set("input.queryPath", \'a"b.jq\')'),
])
def test_setter_messages_include_python_value(name, value, command):
    with pytest.raises(NotImplementedError) as error:
        getattr(RumbleConfiguration(object()), name)(value)
    assert command in str(error.value)
