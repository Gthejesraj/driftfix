import pytest
import yaml

import app


def test_config():
    assert app.load_config("db: {port: 5432}\ndebug: true") == {"db": {"port": 5432}, "debug": True}


def test_documents():
    assert app.load_documents("a: 1\n---\nb: 2\n") == [{"a": 1}, {"b": 2}]


def test_config_files_cannot_run_code():
    with pytest.raises(yaml.YAMLError):
        app.load_config("!!python/object/apply:builtins.len [[1, 2]]")
