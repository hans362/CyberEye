from fastapi import APIRouter
from db import SessionDep
from sqlmodel import select
from models.job import Job, JobCreate, JobRead
from models.error import Error
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError


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
