from urllib.parse import parse_qs

import app


def hello(environ, start_response):
    name = parse_qs(environ["QUERY_STRING"])["name"][0]
    start_response("200 OK", [("Content-Type", "text/plain")])
    return [f"hello {name}".encode()]


def test_greeting():
    with app.make_client(hello) as client:
        assert app.greeting(client, "ada") == "hello ada"
