import app


def test_env(monkeypatch):
    monkeypatch.setenv("APP_DATABASE_URL", "postgres://db")
    monkeypatch.setenv("APP_DEBUG", "true")
    monkeypatch.setenv("SERVICE_API_KEY", "secret")
    s = app.load()
    assert (s.database_url, s.debug, s.api_key) == ("postgres://db", True, "secret")


def test_defaults(monkeypatch):
    monkeypatch.setenv("SERVICE_API_KEY", "k")
    assert app.load().database_url == "sqlite://"
