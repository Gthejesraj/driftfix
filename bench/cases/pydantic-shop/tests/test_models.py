from decimal import Decimal

import pytest
from pydantic import ValidationError

from shop.models import Product


LEGACY = {"productId": 123, "name": "  Mug  ", "price": "9.99"}  # upstream API sends numeric SKUs


def test_legacy_payload_is_normalized():
    p = Product(**LEGACY)
    assert p.sku == "123"
    assert p.name == "Mug"
    assert p.price == Decimal("9.99")


def test_payload_is_camel_case_without_nulls():
    p = Product(**LEGACY)
    assert p.to_payload() == {"productId": "123", "name": "Mug", "price": "9.99"}


def test_populate_by_field_name():
    assert Product(sku="A1", name="Cup", price=1).sku == "A1"


@pytest.mark.parametrize("bad", [{"price": 0}, {"name": ""}, {"color": "red"}])
def test_rejects_invalid(bad):
    with pytest.raises(ValidationError):
        Product(**{**LEGACY, **bad})


def test_color_ok():
    assert Product(**LEGACY, color="#a1b2c3").color == "#a1b2c3"
