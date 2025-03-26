from datetime import datetime
from uuid import uuid4
from sqlmodel import Field, SQLModel


class TaskBase(SQLModel):
    name: str = Field(max_length=128)
    method_name: str = Field(max_length=256)
    input: str = Field()
    output: str = Field()
    status: str = Field(default="pending", max_length=32)
    nonce: str = Field(default="", max_length=128)
    job_id: str = Field(foreign_key="job.id")


class Task(TaskBase, table=True):
    id: str = Field(default=str(uuid4()), primary_key=True)
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(
        default_factory=datetime.now,
        sa_column_kwargs={"onupdate": lambda: datetime.now()},
    )
