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
    error_jobs: int
    total_tasks: int
    error_tasks: int
    domains: int
    ips: int
    services: int
