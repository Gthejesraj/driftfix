import pandas as pd

import app

DF = pd.DataFrame({"name": ["a", "b"], "qty": [1, 3]})


def test_add_row():
    out = app.add_row(DF, {"name": "c", "qty": 5})
    assert out["qty"].tolist() == [1, 3, 5]


def test_totals():
    assert app.column_totals(DF[["qty"]]) == {"qty": 4}


def test_load_series():
    s = app.load_series("x\n1\n2\n")
    assert isinstance(s, pd.Series) and s.tolist() == [1, 2]


def test_csv():
    assert app.to_csv(DF) == "name,qty\na,1\nb,3\n"


def test_averages_skip_text_columns():
    assert app.averages(DF).to_dict() == {"qty": 2.0}
