import app


def test_users():
    engine = app.make_engine()
    app.add_user(engine, "bob")
    app.add_user(engine, "alice")
    assert app.names(engine) == ["alice", "bob"]
    assert app.count(engine) == 2
