import uuid
from datetime import datetime

from sqlmodel import Column, Field, SQLModel, Text

from models.job import JobRead


class TaskBase(SQLModel):
    name: str = Field(max_length=128)
    method_name: str = Field(max_length=256)
    input: str = Field(sa_column=Column(Text))
    output: str = Field(sa_column=Column(Text))
    status: str = Field(default="pending", max_length=32)
    message: str = Field(default="", sa_column=Column(Text))
    nonce: str = Field(default="", max_length=128)
    job_id: uuid.UUID = Field(foreign_key="job.id", ondelete="CASCADE")


class Task(TaskBase, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(
        default_factory=datetime.now,
        sa_column_kwargs={"onupdate": lambda: datetime.now()},
    )


class TaskRead(SQLModel):
    id: uuid.UUID
    name: str
    method_name: str
    input: str
    output: str
    status: str
    message: str
    nonce: str
    job: JobRead
    created_at: datetime
    updated_at: datetime


class TasksRead(SQLModel):
    tasks: list[TaskRead]
    total: int
