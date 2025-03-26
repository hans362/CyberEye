import uuid

from fastapi import APIRouter
from sqlmodel import select

from db import SessionDep
from models.error import Error
from models.job import Job, JobCreate, JobRead, JobTaskRead
from models.task import Task

router = APIRouter(prefix="/jobs", tags=["jobs"])


@router.get("/")
def read_jobs(
    session: SessionDep,
    offset: int = 0,
    limit: int = 100,
) -> list[JobRead]:
    jobs = session.exec(select(Job).offset(offset).limit(limit)).all()
    return jobs


@router.put("/")
def create_job(session: SessionDep, job: JobCreate) -> JobRead | Error:
    try:
        db_job = Job.model_validate(job)
        session.add(db_job)
        session.commit()
        session.refresh(db_job)
        return db_job
    except Exception as e:
        return Error(message=str(e))


@router.get("/{job_id}")
def read_job(job_id: uuid.UUID, session: SessionDep) -> JobRead | Error:
    try:
        job = session.get(Job, job_id)
        if not job:
            return Error(message="测绘项目不存在")
        return job
    except Exception as e:
        return Error(message=str(e))


@router.patch("/{job_id}")
def update_job(
    job_id: uuid.UUID, job: JobCreate, session: SessionDep
) -> JobRead | Error:
    try:
        db_job = session.get(Job, job_id)
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


@router.delete("/{job_id}")
def delete_job(job_id: uuid.UUID, session: SessionDep) -> JobRead | Error:
    try:
        job = session.get(Job, job_id)
        if not job:
            return Error(message="测绘项目不存在")
        session.delete(job)
        session.commit()
        return job
    except Exception as e:
        return Error(message=str(e))


@router.get("/{job_id}/tasks")
def read_job_tasks(job_id: uuid.UUID, session: SessionDep) -> list[JobTaskRead] | Error:
    try:
        job = session.get(Job, job_id)
        if not job:
            return Error(message="测绘项目不存在")
        tasks = session.exec(select(Task).where(Task.job_id == job_id)).all()
        return tasks
    except Exception as e:
        return Error(message=str(e))
