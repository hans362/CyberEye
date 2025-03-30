import uuid
from fastapi import APIRouter, Depends, Request

from models.job import Job
from models.report import IPAddr, Service, SubDomain
from models.task import Task
from models.user import User
from geoip import get_asn, get_city, get_country
from dns import resolver, reversename
from sqlmodel import func, select
from db import SessionDep
from models.error import Error
from models.util import SQLModel, Statistics, IPInfo


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
        q = q.where(Job.status == "error")
        error_jobs = session.exec(q).one()
        q = select(func.count(Task.id))
        try:
            User.is_admin(request, session)
        except Exception:
            q = q.where(Task.job_id == Job.id).where(
                Job.owner_id == uuid.UUID(request.session.get("uid"))
            )
        total_tasks = session.exec(q).one()
        q = q.where(Task.status == "error")
        error_tasks = session.exec(q).one()
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
            error_jobs=error_jobs,
            total_tasks=total_tasks,
            error_tasks=error_tasks,
            domains=domains,
            ips=ips,
            services=services,
        )
    except Exception as e:
        return {"error": str(e)}
