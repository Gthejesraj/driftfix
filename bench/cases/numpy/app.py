import numpy as np


def clean(xs: list[float]) -> np.ndarray:
    a = np.array(xs, dtype=np.float_)
    a[a < 0] = np.NaN
    return a


def total(xs: list[float]) -> float:
    return float(np.product(xs))


def all_positive(xs: list[float]) -> bool:
    return bool(np.alltrue(np.array(xs) > 0))


def as_bytes(xs: list[int]) -> np.ndarray:
    return np.array(xs).astype(np.string_)
