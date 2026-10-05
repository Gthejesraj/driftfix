from decimal import Decimal
from typing import Optional

from pydantic import Field, conlist, constr, root_validator, validator

from shop.base import ShopModel


class Product(ShopModel):
    sku: str = Field(..., alias="productId")
    name: constr(min_length=1)
    price: Decimal
    color: Optional[constr(regex=r"^#[0-9a-f]{6}$")] = None

    @validator("price")
    def positive(cls, v):
        if v <= 0:
            raise ValueError("price must be positive")
        return v


class LineItem(ShopModel):
    product: Product
    quantity: int = 1


class Order(ShopModel):
    items: conlist(LineItem, min_items=1)
    total: Decimal = Decimal(0)

    @root_validator
    def compute_total(cls, values):
        items = values.get("items") or []
        values["total"] = sum((i.product.price * i.quantity for i in items), Decimal(0))
        return values
