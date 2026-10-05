from app import app


def test_price_and_single_warm_up():
    client = app.test_client()
    for _ in range(3):
        body = client.get("/price").get_json()
    assert body == {"price": "9.99", "inits": 1}


def test_greet_escapes():
    assert app.test_client().get("/greet/<x>").get_data(as_text=True) == "<b>&lt;x&gt;</b>"
