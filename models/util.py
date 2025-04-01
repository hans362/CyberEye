import uuid
from sqlmodel import SQLModel


class IPInfo(SQLModel):
    asn: int | str
    asn_organization: str
    city: str
    country: str
    country_code: str
    reverse_dns: str


class Statistics(SQLModel):
    total_jobs: int
    completed_jobs: int
    total_tasks: int
    completed_tasks: int
    domains: int
    ips: int
    services: int


class SearchInput(SQLModel):
    job_id: uuid.UUID | None = None
    domain: str | None = None
    domain_like: str | None = None
    ip: str | None = None
    ip_like: str | None = None
    port: int | None = None
    banner_like: str | None = None
    protocol: str | None = None


class JobInfo(SQLModel):
    id: uuid.UUID
    name: str
