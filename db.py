from typing import Annotated
from fastapi import Depends
from sqlmodel import SQLModel, Session, create_engine

DATABASE_HOST = "localhost"
DATABASE_PORT = 13306
DATABASE_USER = "root"
DATABASE_PASSWORD = "root"
DATABASE_NAME = "cybereye"
DATABASE_URL = f"mysql+pymysql://{DATABASE_USER}:{DATABASE_PASSWORD}@{DATABASE_HOST}:{DATABASE_PORT}/{DATABASE_NAME}?charset=utf8mb4"

engine = create_engine(DATABASE_URL)


def create_db_and_tables():
    SQLModel.metadata.create_all(engine)


def get_session():
    with Session(engine) as session:
        yield session


SessionDep = Annotated[Session, Depends(get_session)]
