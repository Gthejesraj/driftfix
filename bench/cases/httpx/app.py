import httpx


def make_client(wsgi_app) -> httpx.Client:
    return httpx.Client(app=wsgi_app, base_url="http://testserver")


def greeting(client: httpx.Client, name: str) -> str:
    response = client.get("/hello", params={"name": name})
    response.raise_for_status()
    return response.text
