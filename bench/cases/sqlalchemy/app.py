from sqlalchemy import Column, Integer, String, create_engine, select
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()


class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True)
    name = Column(String)


def make_engine():
    engine = create_engine("sqlite://")
    Base.metadata.create_all(engine)
    return engine


def add_user(engine, name: str) -> None:
    with engine.connect() as conn:
        conn.execute(User.__table__.insert(), {"name": name})


def names(engine) -> list[str]:
    return [row[0] for row in engine.execute(select([User.name]).order_by(User.name))]


def count(engine) -> int:
    return engine.execute("SELECT count(*) FROM users").scalar()
