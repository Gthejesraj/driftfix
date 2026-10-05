import app


def test_roundtrip():
    user = app.load({"name": "Ada", "email": "ADA@X.COM"})
    assert app.dump(user) == {"name": "Ada", "email": "ada@x.com"}


def test_from_row():
    class Row:
        name, email = "Bob", "B@Y.COM"
    assert app.from_row(Row()).email == "b@y.com"


def test_tags():
    assert app.tags(["a", "b"]) == ["a", "b"]
