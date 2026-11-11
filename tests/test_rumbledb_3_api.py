import json
from unittest.mock import Mock, patch

import pandas as pd
import pytest
from py4j.protocol import Py4JJavaError

from jsoniq import RumbleSession


@pytest.fixture(scope="module")
def rumble():
    session = (
        RumbleSession.builder.master("local[2]")
        .config("spark.ui.enabled", "false")
        .getOrCreate()
    )
    yield session
    session.stop()
    RumbleSession._rumbleSession = None


@pytest.mark.parametrize("bundled_spark", [False, True])
@pytest.mark.parametrize("show_error_info", [False, True])
def test_builder_rumble_config_before_startup(rumble, monkeypatch, capsys, bundled_spark, show_error_info):
    monkeypatch.setattr(RumbleSession, "_rumbleSession", None)
    builder = (
        RumbleSession.Builder()
        .withBundledSpark(bundled_spark)
        .rumbleConfig("debug.showErrorInfo", show_error_info)
        .rumbleConfig("runtime.resultsSizeCap", 2)
    )
    capsys.readouterr()
    session = builder.getOrCreate()
    assert ("Using RumbleDB jar file" in capsys.readouterr().out) == show_error_info
    assert session.getRumbleConf().getBoolean("debug.showErrorInfo") is show_error_info
    assert session.getRumbleConf().getInt("runtime.resultsSizeCap") == 2
    assert len(session.jsoniq("1 to 3").first()) == 2
    builder.rumbleConfig("debug.showErrorInfo", not show_error_info)
    assert builder.getOrCreate() is session
    assert session.getRumbleConf().getBoolean("debug.showErrorInfo") is not show_error_info
    assert "Using RumbleDB jar file" not in capsys.readouterr().out


def test_configuration_updates_preserve_session_and_other_settings(rumble):
    conf = rumble.getRumbleConf()
    spark = rumble._sparksession._jsparkSession
    rumble.bind("$saved", 42)
    try:
        conf.set("runtime.resultsSizeCap", 2)
        conf.set("debug.showErrorInfo", True)
        assert conf.getInt("runtime.resultsSizeCap") == 2
        assert conf.getBoolean("debug.showErrorInfo") is True
        assert rumble.getRumbleConf() is conf
        assert rumble._sparksession._jsparkSession == spark
        assert rumble.jsoniq("$saved").json() == (42,)
        assert len(rumble.jsoniq("1 to 5").first()) == 2
        assert rumble.jsoniq("1 to 5").json() == (1, 2, 3, 4, 5)
    finally:
        conf.set("runtime.resultsSizeCap", 10)
        conf.set("debug.showErrorInfo", False)
        rumble.unbind("$saved")


def test_materialization_cap_applies_to_new_queries(rumble):
    conf = rumble.getRumbleConf()
    original = conf.getInt("runtime.materializationCap")
    existing = rumble.jsoniq("1 to 3")
    try:
        conf.set("runtime.materializationCap", 2)
        assert existing.json() == (1, 2, 3)
        with pytest.raises(Py4JJavaError, match="Cannot materialize"):
            rumble.jsoniq("1 to 3").json()
    finally:
        conf.set("runtime.materializationCap", original)


@pytest.mark.parametrize("value", [42, 1.5, True, None, "hello", {"a": [1, False, None]}, (1, 2, 3), ([1, 2],)])
def test_python_value_bindings(rumble, value):
    expected = value if isinstance(value, tuple) else (value,)
    assert rumble.jsoniq("$value", value=value).json() == expected
    with pytest.raises(Py4JJavaError):
        rumble.jsoniq("$value")


@pytest.mark.parametrize("values", [(), ({"foo": [42]},) * 10, (1, "two", [3], None)])
def test_generator_bindings(rumble, values):
    generated = (value for value in values)
    rumble.bind("$generated", generated)
    try:
        assert rumble.jsoniq("$generated").json() == values
        assert tuple(generated) == ()
        assert rumble.jsoniq("$temporary", temporary=(value for value in values)).json() == values
    finally:
        rumble.unbind("$generated")


def test_keyword_bindings_restore_persistent_values_even_on_failure(rumble):
    rumble.bind("$value", 7)
    try:
        result = rumble.jsoniq("$value", value=9)
        assert rumble.jsoniq("$value").json() == (7,)
        assert result.json() == (9,)
        with pytest.raises(Py4JJavaError):
            rumble.jsoniq("1 +", value=11)
        assert rumble.jsoniq("$value").json() == (7,)
        with pytest.raises(ValueError):
            rumble.jsoniq("$value", value=11, invalid=[1])
        assert rumble.jsoniq("$value").json() == (7,)
    finally:
        rumble.unbind("$value")


def test_dataframe_and_sequence_bindings(rumble):
    frame = rumble.createDataFrame([(1,), (2,)], ["n"])
    assert sorted(rumble.jsoniq("$rows.n", rows=frame).json()) == [1, 2]
    assert sorted(rumble.jsoniq("$rows.n", rows=frame._jdf).json()) == [1, 2]
    assert sorted(rumble.jsoniq("$rows.n", rows=pd.DataFrame({"n": [1, 2]})).json()) == [1, 2]
    rumble.bindDataFrameAsVariable("$rows", frame)
    try:
        sequence = rumble.jsoniq("$rows")
        assert sorted(rumble.jsoniq("$copy.n", copy=sequence).json()) == [1, 2]
    finally:
        rumble.unbind("$rows")
    local = rumble.jsoniq('(1, "two")')
    assert rumble.jsoniq("$copy", copy=local).json() == (1, "two")
    assert rumble.jsoniq("$copy", copy=local.items()).json() == (1, "two")


def test_item_iteration_and_rdd(rumble):
    sequence = rumble.jsoniq("1 to 3")
    assert [json.loads(item.serializeAsJSON()) for item in sequence.take(2)] == [1, 2]
    sequence.open()
    try:
        assert sequence.hasNext()
        assert sequence.nextJSON() == "1"
    finally:
        sequence.close()
    assert rumble.jsoniq("1 to 3").rdd().collect() == [1, 2, 3]


def test_xquery_uses_xquery_default_without_changing_session(rumble):
    conf = rumble.getRumbleConf()
    language = conf.getString("semantics.queryLanguage")
    result = rumble.xquery("<greeting>{$name}</greeting>", name="World")
    assert result.getRuntimeStaticContext().getSerializationParameters().getMethod() == "xml"
    assert result.serialize() == '<?xml version="1.0" encoding="UTF-8"?><greeting>World</greeting>'
    assert rumble.xquery("map { 'answer': 42 }?answer").json() == (42,)
    assert rumble.xquery('jsoniq version "1.0"; { "answer": 42 }.answer').json() == (42,)
    assert conf.getString("semantics.queryLanguage") == language
    assert rumble.jsoniq('{ "answer": 42 }.answer').json() == (42,)


def test_xquery_preserves_configuration_and_restores_bindings_on_failure(rumble):
    conf = rumble.getRumbleConf()
    cap = conf.getInt("runtime.resultsSizeCap")
    rumble.bind("$saved", 7)
    try:
        conf.set("runtime.resultsSizeCap", 2)
        result = rumble.xquery("$saved, 2, 3", saved=9)
        assert result.json() == (9, 2, 3)
        assert len(result.first()) == 2
        assert rumble.xquery("$saved").json() == (7,)
        with pytest.raises(Py4JJavaError):
            rumble.xquery("1 +", saved=11)
        assert rumble.jsoniq("$saved").json() == (7,)
        with pytest.raises(ValueError):
            rumble.xquery("$saved", saved=11, invalid=[1])
        assert rumble.xquery("$saved").json() == (7,)
    finally:
        conf.set("runtime.resultsSizeCap", cap)
        rumble.unbind("$saved")


def test_notebook_extension_and_display(rumble, capsys):
    pytest.importorskip("IPython")
    from jsoniqmagic import JSONiqMagic, load_ipython_extension

    shell = Mock()
    with patch.object(RumbleSession.Builder, "getOrCreate", return_value=rumble):
        load_ipython_extension(shell)
        shell.register_magics.assert_called_once_with(JSONiqMagic)
        assert "xquery" in JSONiqMagic.magics["cell"]
        assert rumble.getRumbleConf().getInt("runtime.resultsSizeCap") == 10
        rumble.getRumbleConf().set("runtime.resultsSizeCap", 2)
        try:
            JSONiqMagic().run("", "1 to 3")
            output = capsys.readouterr().out
            assert "Displaying the first 2 items" in output
            assert output.endswith("1\n2\n")
            serialized = rumble.jsoniq("1 to 3").serialize()
            JSONiqMagic().jsoniq("-s", "1 to 3")
            assert capsys.readouterr().out == serialized + "\n"
            query = "<greeting>Hello</greeting>"
            JSONiqMagic().xquery("", query)
            assert capsys.readouterr().out == '<?xml version="1.0" encoding="UTF-8"?><greeting>Hello</greeting>\n'
            JSONiqMagic().xquery("", '''
                declare namespace output = "http://www.w3.org/2010/xslt-xquery-serialization";
                declare option output:method "text";
                <greeting>Hello</greeting>
            ''')
            assert capsys.readouterr().out == "Hello\n"
            JSONiqMagic().xquery("-j", "1 to 3")
            output = capsys.readouterr().out
            assert "Displaying the first 2 items" in output
            assert output.endswith("1\n2\n")
        finally:
            rumble.getRumbleConf().set("runtime.resultsSizeCap", 10)
