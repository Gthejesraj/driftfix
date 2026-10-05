from pydantic import BaseModel, validator


class User(BaseModel):
    name: str
    email: str

    class Config:
        orm_mode = True

    @validator("email")
    def lowercase(cls, v):
        return v.lower()


class Tags(BaseModel):
    __root__: list[str]


def load(data: dict) -> User:
    return User.parse_obj(data)


def dump(user: User) -> dict:
    return user.dict()


def from_row(row) -> User:
    return User.from_orm(row)


def tags(raw: list[str]) -> list[str]:
    return Tags.parse_obj(raw).__root__
