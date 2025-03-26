import uuid
from datetime import datetime

from sqlmodel import Column, Field, SQLModel, Text


class JobBase(SQLModel):
    name: str = Field(max_length=128)
    domain: str = Field(max_length=256)
    description: str = Field(sa_column=Column(Text))
    status: str = Field(default="pending", max_length=32)
    message: str = Field(default="", sa_column=Column(Text))
    owner_id: uuid.UUID = Field(foreign_key="user.id", ondelete="CASCADE")


class Job(JobBase, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(
        default_factory=datetime.now,
        sa_column_kwargs={"onupdate": lambda: datetime.now()},
    )


class JobCreate(SQLModel):
    name: str
    domain: str
    description: str
    owner_id: uuid.UUID  # TODO: remove this field


class JobRead(SQLModel):
    id: uuid.UUID
    name: str
    domain: str
    description: str
    status: str
    message: str
    owner_id: uuid.UUID
    created_at: datetime
    updated_at: datetime


class JobTaskRead(SQLModel):
    id: uuid.UUID
    name: str
    method_name: str
    status: str
    message: str
    created_at: datetime
    updated_at: datetime
