from PIL import Image

import app


def test_thumbnail():
    out = app.thumbnail(Image.new("RGB", (64, 32), "red"), (16, 8))
    assert out.size == (16, 8) and out.getpixel((4, 4)) == (255, 0, 0)


def test_text_width():
    assert app.text_width("hello world") > app.text_width("hi") > 0
