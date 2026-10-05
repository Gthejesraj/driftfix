from shop.base import ShopModel
from shop.models import Product


class Catalog(ShopModel):
    __root__: list[Product]

    def skus(self) -> list[str]:
        return [p.sku for p in self.__root__]


def parse_catalog(raw_json: str) -> Catalog:
    return Catalog.parse_raw(raw_json)
