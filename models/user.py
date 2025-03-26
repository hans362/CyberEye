import uuid
from datetime import datetime

from fastapi import HTTPException, Request
from sqlmodel import Field, SQLModel, select

from db import SessionDep


class UserBase(SQLModel):
    username: str = Field(max_length=32, unique=True)
    password: str = Field(max_length=256)
    role: str = Field(max_length=32)


class User(UserBase, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(
        default_factory=datetime.now,
        sa_column_kwargs={"onupdate": lambda: datetime.now()},
    )

    @staticmethod
    def is_authenticated(request: Request, session: SessionDep) -> None:
        if (
            not request.session.get("uid")
            or not session.exec(
                select(User).where(User.id == uuid.UUID(request.session.get("uid")))
            ).first()
        ):
            request.session.clear()
            raise HTTPException(status_code=401, detail="Unauthenticated")
        return session.exec(
            select(User).where(User.id == uuid.UUID(request.session.get("uid")))
        ).first()

    @staticmethod
    def is_admin(request: Request, session: SessionDep) -> None:
        if (
            not request.session.get("uid")
            or not session.exec(
                select(User).where(User.id == uuid.UUID(request.session.get("uid")))
            ).first()
            or session.exec(
                select(User).where(User.id == uuid.UUID(request.session.get("uid")))
            )
            .first()
            .role
            != "admin"
        ):
            request.session.clear()
            raise HTTPException(status_code=401, detail="Unauthenticated")
        return session.exec(
            select(User).where(User.id == uuid.UUID(request.session.get("uid")))
        ).first()


class UserRead(SQLModel):
    id: uuid.UUID
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
