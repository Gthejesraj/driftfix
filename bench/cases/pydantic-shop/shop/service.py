from decimal import Decimal

from shop.models import LineItem, Order, Product


def discounted(product: Product, percent: int) -> Product:
    new_price = (product.price * (100 - percent) / 100).quantize(Decimal("0.01"))
    return product.copy(update={"price": new_price})


def place_order(rows: list[dict]) -> Order:
    return Order(items=[LineItem.parse_obj(r) for r in rows])


def product_fields() -> list[str]:
    return list(Product.__fields__)


def product_from_record(record) -> Product:
    return Product.from_orm(record)
