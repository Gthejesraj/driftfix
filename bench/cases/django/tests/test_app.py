from django.test import Client


def test_status():
    body = Client().get("/status/").json()
    assert body == {"message": "ok", "since": "2020-01-01T00:00:00+00:00", "ajax": False}


def test_status_ajax():
    body = Client().get("/status/", HTTP_X_REQUESTED_WITH="XMLHttpRequest").json()
    assert body["ajax"] is True
