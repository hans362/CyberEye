from datetime import datetime
from uuid import uuid4
from sqlmodel import Field, SQLModel


class UserBase(SQLModel):
    username: str = Field(max_length=32, unique=True)
    password: str = Field(max_length=256)
    role: str = Field(max_length=32)


class User(UserBase, table=True):
    id: str = Field(default=str(uuid4()), primary_key=True)
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(
        default_factory=datetime.now,
        sa_column_kwargs={"onupdate": lambda: datetime.now()},
    )


class UserRead(SQLModel):
    id: str
    username: str
    role: str
    created_at: datetime
    updated_at: datetime


class UserCreate(SQLModel):
    username: str
    password: str
    role: str


class UserUpdate(SQLModel):
    username: str | None = None
    password: str | None = None
    role: str | None = None


class UserLogin(SQLModel):
    username: str
    password: str
