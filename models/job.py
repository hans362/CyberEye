from datetime import datetime
from uuid import uuid4
from sqlmodel import Field, SQLModel


class JobBase(SQLModel):
    name: str = Field(max_length=128)
    domain: str = Field(max_length=256)
    description: str = Field()
    status: str = Field(
        default="pending", max_length=32
    )  # pending, running, completed, failed
    owner_id: str = Field(foreign_key="user.id")


class Job(JobBase, table=True):
    id: str = Field(default=str(uuid4()), primary_key=True)
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(
        default_factory=datetime.now,
        sa_column_kwargs={"onupdate": lambda: datetime.now()},
    )


class JobCreate(SQLModel):
    name: str
    domain: str
    description: str
    owner_id: str # TODO: remove this field


class JobRead(SQLModel):
    id: str
    name: str
    domain: str
    description: str
    status: str
    owner_id: str
    created_at: datetime
    updated_at: datetime
