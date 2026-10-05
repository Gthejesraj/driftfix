import math

import app


def test_clean():
    out = app.clean([1.0, -1.0])
    assert out[0] == 1.0 and math.isnan(out[1])


def test_math():
    assert app.total([2, 3]) == 6
    assert app.all_positive([1, 2]) and not app.all_positive([1, -2])


def test_bytes():
    assert app.as_bytes([1, 22]).tolist() == [b"1", b"22"]
