import uuid
from fastapi import APIRouter, Depends, Request

from config import SERVICE_SCAN_KEYWORDS
from models.job import Job, JobServiceRead, JobServicesRead
from models.report import IPAddr, Service, SubDomain, SubDomainIPAddr
from models.task import Task
from models.user import User
from geoip import get_asn, get_city, get_country
from dns import resolver, reversename
from sqlmodel import func, select
from db import SessionDep
from models.error import Error
from models.util import JobInfo, SearchInput, Statistics, IPInfo


router = APIRouter(prefix="/utils", tags=["utils"])


@router.get("/ip/{ip}", dependencies=[Depends(User.is_authenticated)])
def ip_info(ip: str) -> IPInfo:
    asn = get_asn(ip)
    city = get_city(ip)
    country = get_country(ip)
    try:
        reverse_dns = resolver.query(reversename.from_address(ip), "PTR")
    except Exception:
        reverse_dns = []
    ip_info = {
        "asn": asn.get("autonomous_system_number", "未知") if asn else "未知",
        "asn_organization": (
            asn.get("autonomous_system_organization", "未知") if asn else "未知"
        ),
        "city": (
            city.get("city", {}).get("names", {}).get("en", "未知") if city else "未知"
        ),
        "country": (
            country.get("country", {}).get("names", {}).get("en", "未知")
            if country
            else "未知"
        ),
        "country_code": (
            country.get("country", {}).get("iso_code", "未知") if country else "未知"
        ),
        "reverse_dns": str(reverse_dns[0]) if len(reverse_dns) > 0 else "未知",
    }
    return IPInfo(**ip_info)


@router.get("/statistics", dependencies=[Depends(User.is_authenticated)])
def statistics(request: Request, session: SessionDep) -> Statistics | Error:
    try:
        q = select(func.count(Job.id))
        try:
            User.is_admin(request, session)
        except Exception:
            q = q.where(Job.owner_id == uuid.UUID(request.session.get("uid")))
        total_jobs = session.exec(q).one()
        q = q.where(Job.status == "completed")
        completed_jobs = session.exec(q).one()
        q = select(func.count(Task.id))
        try:
            User.is_admin(request, session)
        except Exception:
            q = q.where(Task.job_id == Job.id).where(
                Job.owner_id == uuid.UUID(request.session.get("uid"))
            )
        total_tasks = session.exec(q).one()
        q = q.where(Task.status == "completed")
        completed_tasks = session.exec(q).one()
        q = select(func.count(SubDomain.id))
        try:
            User.is_admin(request, session)
        except Exception:
            q = q.where(SubDomain.job_id == Job.id).where(
                Job.owner_id == uuid.UUID(request.session.get("uid"))
            )
        domains = session.exec(q).one()
        q = select(func.count(IPAddr.id))
        try:
            User.is_admin(request, session)
        except Exception:
            q = q.where(IPAddr.job_id == Job.id).where(
                Job.owner_id == uuid.UUID(request.session.get("uid"))
            )
        ips = session.exec(q).one()
        q = select(func.count(Service.id))
        try:
            User.is_admin(request, session)
        except Exception:
            q = (
                q.where(Service.ip_id == IPAddr.id)
                .where(IPAddr.job_id == Job.id)
                .where(Job.owner_id == uuid.UUID(request.session.get("uid")))
            )
        services = session.exec(q).one()
        return Statistics(
            total_jobs=total_jobs,
            completed_jobs=completed_jobs,
            total_tasks=total_tasks,
            completed_tasks=completed_tasks,
            domains=domains,
            ips=ips,
            services=services,
        )
    except Exception as e:
        return {"error": str(e)}


@router.post("/search", dependencies=[Depends(User.is_authenticated)])
def search(
    request: Request,
    session: SessionDep,
    search: SearchInput,
    limit: int = 10,
    offset: int = 0,
) -> JobServicesRead | Error:
    try:
        q = (
            select(Service, IPAddr.ip, SubDomain.domain)
            .join(IPAddr, Service.ip_id == IPAddr.id)
            .join(SubDomainIPAddr, SubDomainIPAddr.ip_id == IPAddr.id)
            .join(SubDomain, SubDomainIPAddr.subdomain_id == SubDomain.id)
            .join(Job, Job.id == IPAddr.job_id)
        )
        try:
            User.is_admin(request, session)
        except Exception:
            q = q.where(Job.owner_id == uuid.UUID(request.session.get("uid")))
        if search.job_id:
            q = q.where(Job.id == search.job_id)
        if search.domain:
            q = q.where(SubDomain.domain == search.domain)
        if search.domain_like:
            q = q.where(SubDomain.domain.like(f"%{search.domain_like}%"))
        if search.ip:
            q = q.where(IPAddr.ip == search.ip)
        if search.ip_like:
            q = q.where(IPAddr.ip.like(f"%{search.ip_like}%"))
        if search.port:
            q = q.where(Service.port == search.port)
        if search.banner_like:
            q = q.where(Service.banner.like(f"%{search.banner_like}%"))
        if search.protocol:
            q = q.where(Service.protocol == search.protocol)
        total = session.exec(select(func.count()).select_from(q)).one()
        q = q.order_by(Service.created_at.desc()).offset(offset).limit(limit)
        results = session.exec(q).all()
        return JobServicesRead(
            services=[
                JobServiceRead(
                    **service.model_dump(),
                    ip=ip,
                    domain=domain,
                )
                for service, ip, domain in results
            ],
            total=total,
        )
    except Exception as e:
        return Error(message=str(e))


@router.get("/search/jobs", dependencies=[Depends(User.is_authenticated)])
def search_jobs(
    request: Request,
    session: SessionDep,
    name: str | None = None,
) -> list[JobInfo] | Error:
    try:
        q = select(Job)
        try:
            User.is_admin(request, session)
        except Exception:
            q = q.where(Job.owner_id == uuid.UUID(request.session.get("uid")))
        if name:
            q = q.where(Job.name.like(f"%{name}%"))
        q = q.order_by(Job.created_at.desc()).limit(10)
        return session.exec(q).all()
    except Exception as e:
        return Error(message=str(e))


@router.get("/search/protocols", dependencies=[Depends(User.is_authenticated)])
def search_protocols() -> list[str]:
    return ["HTTP", "HTTPS"] + SERVICE_SCAN_KEYWORDS.keys()
