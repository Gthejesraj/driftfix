import json
from decimal import Decimal

import pytest
from pydantic import ValidationError

from shop.catalog import parse_catalog
from shop.service import discounted, place_order, product_fields, product_from_record
from shop.models import Product

MUG = {"productId": "M1", "name": "Mug", "price": "10.00"}


def test_discount_does_not_mutate():
    p = Product(**MUG)
    d = discounted(p, 15)
    assert (p.price, d.price) == (Decimal("10.00"), Decimal("8.50"))


def test_order_total():
    order = place_order([{"product": MUG, "quantity": 3}, {"product": {**MUG, "price": "1.50"}}])
    assert order.total == Decimal("31.50")
    assert order.to_payload()["total"] == "31.50"


def test_empty_order_rejected():
    with pytest.raises(ValidationError):
        place_order([])


def test_catalog():
    assert parse_catalog(json.dumps([MUG, {**MUG, "productId": "M2"}])).skus() == ["M1", "M2"]


def test_fields():
    assert product_fields() == ["sku", "name", "price", "color"]


def test_from_record():
    class Record:
        sku, name, price, color = "R1", "Plate", Decimal(3), None
    assert product_from_record(Record()).sku == "R1"
