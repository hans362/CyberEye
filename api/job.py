import uuid

from fastapi import APIRouter, Depends, Request
from sqlmodel import func, outerjoin, select

from db import SessionDep
from models.error import Error
from models.job import (
    Job,
    JobCreate,
    JobDomainsRead,
    JobIPsRead,
    JobRead,
    JobServiceRead,
    JobServicesRead,
    JobsRead,
    JobTasksRead,
)
from models.report import IPAddr, Service, SubDomain, SubDomainIPAddr
from models.task import Task
from models.user import User

router = APIRouter(prefix="/jobs", tags=["jobs"])


@router.get("/", dependencies=[Depends(User.is_authenticated)])
def read_jobs(
    request: Request,
    session: SessionDep,
    offset: int = 0,
    limit: int = 100,
) -> JobsRead:
    q = select(Job)
    q_total = select(func.count(Job.id))
    try:
        User.is_admin(request, session)
    except Exception:
        q = q.where(Job.owner_id == uuid.UUID(request.session.get("uid")))
        q_total = q_total.where(Job.owner_id == uuid.UUID(request.session.get("uid")))
    q = q.order_by(Job.created_at.desc()).offset(offset).limit(limit)
    jobs = session.exec(q).all()
    total = session.exec(q_total).one()
    return JobsRead(jobs=jobs, total=total)


@router.put("/", dependencies=[Depends(User.is_authenticated)])
def create_job(
    request: Request, session: SessionDep, job: JobCreate
) -> JobRead | Error:
    try:
        job.owner_id = uuid.UUID(request.session.get("uid"))
        db_job = Job.model_validate(job)
        session.add(db_job)
        session.commit()
        session.refresh(db_job)
        return db_job
    except Exception as e:
        return Error(message=str(e))


@router.get("/{job_id}", dependencies=[Depends(User.is_authenticated)])
def read_job(
    request: Request, job_id: uuid.UUID, session: SessionDep
) -> JobRead | Error:
    try:
        q = select(Job).where(Job.id == job_id)
        try:
            User.is_admin(request, session)
        except Exception:
            q = q.where(Job.owner_id == uuid.UUID(request.session.get("uid")))
        job = session.exec(q).first()
        if not job:
            return Error(message="测绘项目不存在")
        return job
    except Exception as e:
        return Error(message=str(e))


@router.patch("/{job_id}", dependencies=[Depends(User.is_authenticated)])
def update_job(
    request: Request, job_id: uuid.UUID, job: JobCreate, session: SessionDep
) -> JobRead | Error:
    try:
        q = select(Job).where(Job.id == job_id)
        try:
            User.is_admin(request, session)
        except Exception:
            q = q.where(Job.owner_id == uuid.UUID(request.session.get("uid")))
        db_job = session.exec(q).first()
        if not db_job:
            return Error(message="测绘项目不存在")
        if job.name:
            db_job.name = job.name
        if job.domain:
            db_job.domain = job.domain
        if job.description:
            db_job.description = job.description
        session.add(db_job)
        session.commit()
        session.refresh(db_job)
        return db_job
    except Exception as e:
        return Error(message=str(e))


@router.delete("/{job_id}", dependencies=[Depends(User.is_authenticated)])
def delete_job(
    request: Request, job_id: uuid.UUID, session: SessionDep
) -> JobRead | Error:
    try:
        q = select(Job).where(Job.id == job_id)
        try:
            User.is_admin(request, session)
        except Exception:
            q = q.where(Job.owner_id == uuid.UUID(request.session.get("uid")))
        job = session.exec(q).first()
        if not job:
            return Error(message="测绘项目不存在")
        session.delete(job)
        session.commit()
        return job
    except Exception as e:
        return Error(message=str(e))


@router.get("/{job_id}/tasks", dependencies=[Depends(User.is_authenticated)])
def read_job_tasks(
    request: Request, job_id: uuid.UUID, session: SessionDep
) -> JobTasksRead | Error:
    try:
        q = select(Job).where(Job.id == job_id)
        try:
            User.is_admin(request, session)
        except Exception:
            q = q.where(Job.owner_id == uuid.UUID(request.session.get("uid")))
        job = session.exec(q).first()
        if not job:
            return Error(message="测绘项目不存在")
        tasks = session.exec(
            select(Task).where(Task.job_id == job_id).order_by(Task.created_at.desc())
        ).all()
        return JobTasksRead(tasks=tasks, total=len(tasks))
    except Exception as e:
        return Error(message=str(e))


@router.get("/{job_id}/domains", dependencies=[Depends(User.is_authenticated)])
def read_job_domains(
    request: Request,
    job_id: uuid.UUID,
    session: SessionDep,
    search: str = "",
    offset: int = 0,
    limit: int = 100,
) -> JobDomainsRead | Error:
    try:
        q = select(Job).where(Job.id == job_id)
        try:
            User.is_admin(request, session)
        except Exception:
            q = q.where(Job.owner_id == uuid.UUID(request.session.get("uid")))
        job = session.exec(q).first()
        if not job:
            return Error(message="测绘项目不存在")
        domains_ids = session.exec(
            select(SubDomain.id)
            .where(SubDomain.job_id == job_id)
            .where(SubDomain.domain.like(f"%{search}%"))
            .order_by(SubDomain.domain)
            .offset(offset)
            .limit(limit)
        ).all()
        results = session.exec(
            select(SubDomain.domain, IPAddr.ip)
            .where(SubDomain.id.in_(domains_ids))
            .select_from(
                outerjoin(
                    SubDomain,
                    SubDomainIPAddr,
                    SubDomain.id == SubDomainIPAddr.subdomain_id,
                ).outerjoin(IPAddr, IPAddr.id == SubDomainIPAddr.ip_id)
            )
            .order_by(SubDomain.domain)
        ).all()
        domains = {}
        for domain, ip in results:
            if domain not in domains:
                domains[domain] = []
            if ip:
                domains[domain].append(ip)
        return JobDomainsRead(
            domains=[{"domain": domain, "ips": domains[domain]} for domain in domains],
            total=session.exec(
                select(func.count(SubDomain.id))
                .where(SubDomain.job_id == job_id)
                .where(SubDomain.domain.like(f"%{search}%"))
            ).one(),
        )
    except Exception as e:
        return Error(message=str(e))


@router.get("/{job_id}/ips", dependencies=[Depends(User.is_authenticated)])
def read_job_ips(
    request: Request,
    job_id: uuid.UUID,
    session: SessionDep,
    search: str = "",
    offset: int = 0,
    limit: int = 100,
) -> JobIPsRead | Error:
    try:
        q = select(Job).where(Job.id == job_id)
        try:
            User.is_admin(request, session)
        except Exception:
            q = q.where(Job.owner_id == uuid.UUID(request.session.get("uid")))
        job = session.exec(q).first()
        if not job:
            return Error(message="测绘项目不存在")
        ips_ids = session.exec(
            select(IPAddr.id)
            .where(IPAddr.job_id == job_id)
            .where(IPAddr.ip.like(f"%{search}%"))
            .order_by(IPAddr.ip)
            .offset(offset)
            .limit(limit)
        ).all()
        results = session.exec(
            select(IPAddr, SubDomain.domain)
            .where(IPAddr.id.in_(ips_ids))
            .select_from(
                outerjoin(
                    IPAddr,
                    SubDomainIPAddr,
                    IPAddr.id == SubDomainIPAddr.ip_id,
                ).outerjoin(SubDomain, SubDomain.id == SubDomainIPAddr.subdomain_id)
            )
            .order_by(IPAddr.ip)
        ).all()
        ips = {}
        for ip, domain in results:
            if ip.ip not in ips:
                ips[ip.ip] = [[], [int(port) for port in ip.ports.split(",") if port]]
            if domain:
                ips[ip.ip][0].append(domain)
        return JobIPsRead(
            ips=[{"ip": ip, "domains": ips[ip][0], "ports": ips[ip][1]} for ip in ips],
            total=session.exec(
                select(func.count(IPAddr.id))
                .where(IPAddr.job_id == job_id)
                .where(IPAddr.ip.like(f"%{search}%"))
            ).one(),
        )
    except Exception as e:
        return Error(message=str(e))


@router.get("/{job_id}/services", dependencies=[Depends(User.is_authenticated)])
def read_job_services(
    request: Request,
    job_id: uuid.UUID,
    session: SessionDep,
    offset: int = 0,
    limit: int = 100,
) -> JobServicesRead | Error:
    try:
        q = select(Job).where(Job.id == job_id)
        try:
            User.is_admin(request, session)
        except Exception:
            q = q.where(Job.owner_id == uuid.UUID(request.session.get("uid")))
        job = session.exec(q).first()
        if not job:
            return Error(message="测绘项目不存在")
        results = session.exec(
            select(Service, IPAddr.ip, SubDomain.domain)
            .join(IPAddr, Service.ip_id == IPAddr.id)
            .join(SubDomainIPAddr, SubDomainIPAddr.ip_id == IPAddr.id)
            .join(SubDomain, SubDomainIPAddr.subdomain_id == SubDomain.id)
            .where(IPAddr.job_id == job_id)
            .order_by(Service.created_at.desc())
            .offset(offset)
            .limit(limit)
        ).all()
        return JobServicesRead(
            services=[
                JobServiceRead(
                    **service.model_dump(),
                    ip=ip,
                    domain=domain,
                )
                for service, ip, domain in results
            ],
            total=session.exec(
                select(func.count()).select_from(
                    select(Service, IPAddr.ip, SubDomain.domain)
                    .join(IPAddr, Service.ip_id == IPAddr.id)
                    .join(SubDomainIPAddr, SubDomainIPAddr.ip_id == IPAddr.id)
                    .join(SubDomain, SubDomainIPAddr.subdomain_id == SubDomain.id)
                    .where(IPAddr.job_id == job_id)
                )
            ).one(),
        )
    except Exception as e:
        return Error(message=str(e))
