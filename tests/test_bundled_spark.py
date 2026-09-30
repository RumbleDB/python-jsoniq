import os
from unittest.mock import Mock, patch

import pytest

from jsoniq import RumbleSession


@pytest.fixture
def builder(monkeypatch):
    monkeypatch.setattr(RumbleSession, "_rumbleSession", None)
    spark_builder = Mock()
    with patch("jsoniq.session.os.popen") as popen, patch("jsoniq.session.SparkSession") as spark:
        popen.return_value.read.return_value = 'openjdk version "17.0.1"'
        spark.builder.config.return_value = spark_builder
        return RumbleSession.Builder()


def set_spark_home(monkeypatch, value):
    if value is None:
        monkeypatch.delenv("SPARK_HOME", raising=False)
    else:
        monkeypatch.setenv("SPARK_HOME", value)


@pytest.mark.parametrize("method", ["getOrCreate", "create"])
@pytest.mark.parametrize("original", [None, "", "/external/spark"])
def test_bundled_spark_restores_environment_after_startup(builder, monkeypatch, method, original):
    set_spark_home(monkeypatch, original)
    spark_session = Mock()

    def start():
        assert "SPARK_HOME" not in os.environ
        # Also restore absence if startup itself changes the environment.
        os.environ["SPARK_HOME"] = "/startup/spark"
        return spark_session

    getattr(builder._sparkbuilder, method).side_effect = start
    result = getattr(builder, method)()
    assert result._sparksession is spark_session
    assert os.environ.get("SPARK_HOME") == original
    assert ("SPARK_HOME" in os.environ) == (original is not None)


@pytest.mark.parametrize("method", ["getOrCreate", "create"])
@pytest.mark.parametrize("original", [None, "", "/external/spark"])
@pytest.mark.parametrize("error_type", [RuntimeError, FileNotFoundError, TypeError, SystemExit])
def test_bundled_spark_restores_environment_after_failure(builder, monkeypatch, method, original, error_type):
    set_spark_home(monkeypatch, original)
    failure = error_type("Startup failed")

    def start():
        assert "SPARK_HOME" not in os.environ
        raise failure

    getattr(builder._sparkbuilder, method).side_effect = start
    with pytest.raises(error_type) as error:
        getattr(builder, method)()
    assert error.value is failure
    assert os.environ.get("SPARK_HOME") == original
    assert ("SPARK_HOME" in os.environ) == (original is not None)
    assert RumbleSession._rumbleSession is None


@pytest.mark.parametrize("method", ["getOrCreate", "create"])
def test_external_spark_opt_out_preserves_environment(builder, monkeypatch, method):
    monkeypatch.setenv("SPARK_HOME", "/external/spark")

    def start():
        assert os.environ["SPARK_HOME"] == "/external/spark"
        return Mock()

    getattr(builder._sparkbuilder, method).side_effect = start
    assert builder.withBundledSpark(False) is builder
    getattr(builder, method)()
    assert os.environ["SPARK_HOME"] == "/external/spark"


def test_get_or_create_reuses_existing_session(builder, monkeypatch):
    existing = Mock()
    monkeypatch.setattr(RumbleSession, "_rumbleSession", existing)
    monkeypatch.setenv("SPARK_HOME", "/external/spark")
    assert builder.getOrCreate() is existing
    builder._sparkbuilder.getOrCreate.assert_not_called()
    assert os.environ["SPARK_HOME"] == "/external/spark"


def test_bundled_spark_can_be_reenabled(builder, monkeypatch):
    monkeypatch.setenv("SPARK_HOME", "/external/spark")
    builder.withBundledSpark(False)
    assert builder.withBundledSpark() is builder

    def start():
        assert "SPARK_HOME" not in os.environ
        return Mock()

    builder._sparkbuilder.getOrCreate.side_effect = start
    builder.getOrCreate()
    assert os.environ["SPARK_HOME"] == "/external/spark"


def test_bundled_spark_starts_with_invalid_external_home(monkeypatch, tmp_path):
    monkeypatch.setattr(RumbleSession, "_rumbleSession", None)
    invalid_home = str(tmp_path / "missing-spark")
    monkeypatch.setenv("SPARK_HOME", invalid_home)
    session = None
    try:
        session = (
            RumbleSession.Builder().master("local[2]")
            .config("spark.ui.enabled", "false").getOrCreate()
        )
        assert session.version == "4.0.3"
        assert session.jsoniq("1 + 1").json() == (2,)
        assert os.environ["SPARK_HOME"] == invalid_home
    finally:
        if session is not None:
            session.stop()
