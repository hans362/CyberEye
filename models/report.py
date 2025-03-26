from datetime import datetime
from uuid import uuid4
from sqlmodel import Field, SQLModel


class SubDomainBase(SQLModel):
    domain: str = Field(max_length=256)
    job_id: str = Field(foreign_key="job.id")


class SubDomain(SubDomainBase, table=True):
    id: str = Field(default=str(uuid4()), primary_key=True)
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(
        default_factory=datetime.now,
        sa_column_kwargs={"onupdate": lambda: datetime.now()},
    )


class IPAddrBase(SQLModel):
    ip: str = Field(max_length=256)
    ports: str = Field()
    job_id: str = Field(foreign_key="job.id")


class IPAddr(IPAddrBase, table=True):
    id: str = Field(default=str(uuid4()), primary_key=True)
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(
        default_factory=datetime.now,
        sa_column_kwargs={"onupdate": lambda: datetime.now()},
    )


class SubDomainIPAddr(SQLModel, table=True):
    id: str = Field(default=str(uuid4()), primary_key=True)
    subdomain_id: str = Field(foreign_key="subdomain.id")
    ip_id: str = Field(foreign_key="ipaddr.id")


class ServiceBase(SQLModel):
    ip_id: str = Field(foreign_key="ipaddr.id")
    port: int = Field()
    banner: str = Field()
    protocol: str = Field()


class Service(ServiceBase, table=True):
    id: str = Field(default=str(uuid4()), primary_key=True)
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(
        default_factory=datetime.now,
        sa_column_kwargs={"onupdate": lambda: datetime.now()},
    )
