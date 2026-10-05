import io

import pandas as pd


def add_row(df: pd.DataFrame, row: dict) -> pd.DataFrame:
    return df.append(row, ignore_index=True)


def column_totals(df: pd.DataFrame) -> dict:
    return {name: col.sum() for name, col in df.iteritems()}


def load_series(csv_text: str) -> pd.Series:
    return pd.read_csv(io.StringIO(csv_text), squeeze=True)


def to_csv(df: pd.DataFrame) -> str:
    return df.to_csv(index=False, line_terminator="\n")


def averages(df: pd.DataFrame) -> pd.Series:
    """Average of every numeric column in a mixed table."""
    return df.mean()
