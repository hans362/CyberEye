import uuid

from fastapi import APIRouter, Depends, Request
from sqlmodel import func, select

from db import SessionDep
from models.error import Error
from models.job import Job, JobCreate, JobRead, JobsRead, JobTasksRead
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
