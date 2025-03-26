from datetime import datetime
import uuid
from sqlmodel import Column, Field, SQLModel, Text


class SubDomainBase(SQLModel):
    domain: str = Field(max_length=256)
    job_id: uuid.UUID = Field(foreign_key="job.id")


class SubDomain(SubDomainBase, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(
        default_factory=datetime.now,
        sa_column_kwargs={"onupdate": lambda: datetime.now()},
    )


class IPAddrBase(SQLModel):
    ip: str = Field(max_length=256)
    ports: str = Field(default="", sa_column=Column(Text))
    job_id: uuid.UUID = Field(foreign_key="job.id")


class IPAddr(IPAddrBase, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(
        default_factory=datetime.now,
        sa_column_kwargs={"onupdate": lambda: datetime.now()},
    )


class SubDomainIPAddr(SQLModel, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    subdomain_id: uuid.UUID = Field(foreign_key="subdomain.id")
    ip_id: uuid.UUID = Field(foreign_key="ipaddr.id")


class ServiceBase(SQLModel):
    ip_id: uuid.UUID = Field(foreign_key="ipaddr.id")
    port: int = Field()
    banner: str = Field(sa_column=Column(Text))
    protocol: str = Field(sa_column=Column(Text))


class Service(ServiceBase, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(
        default_factory=datetime.now,
        sa_column_kwargs={"onupdate": lambda: datetime.now()},
    )
