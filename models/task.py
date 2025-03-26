from datetime import datetime
import uuid
from sqlmodel import Column, Field, SQLModel, Text


class TaskBase(SQLModel):
    name: str = Field(max_length=128)
    method_name: str = Field(max_length=256)
    input: str = Field(sa_column=Column(Text))
    output: str = Field(sa_column=Column(Text))
    status: str = Field(default="pending", max_length=32)
    nonce: str = Field(default="", max_length=128)
    job_id: uuid.UUID = Field(foreign_key="job.id")


class Task(TaskBase, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(
        default_factory=datetime.now,
        sa_column_kwargs={"onupdate": lambda: datetime.now()},
    )
