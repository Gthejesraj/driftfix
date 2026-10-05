import json
from decimal import Decimal

from pydantic import BaseModel


class ShopModel(BaseModel):
    """Base for every model in the shop. Payloads go out camelCase, without nulls."""

    class Config:
        orm_mode = True
        allow_population_by_field_name = True
        anystr_strip_whitespace = True
        json_encoders = {Decimal: str}

    def to_payload(self) -> dict:
        return json.loads(self.json(by_alias=True, exclude_none=True))
