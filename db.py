from typing import Annotated
from fastapi import Depends, FastAPI, Request
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlmodel import SQLModel, Session, create_engine, select
from models.user import User
from models.task import Task
from models.job import Job
from models.report import SubDomain, IPAddr, SubDomainIPAddr, Service

database_name = "cybereye"
database_url = f"mysql+pymysql://root:root@localhost:13306/{database_name}?charset=utf8mb4"

engine = create_engine(database_url)


def create_db_and_tables():
    SQLModel.metadata.create_all(engine)


def get_session():
    with Session(engine) as session:
        yield session


SessionDep = Annotated[Session, Depends(get_session)]