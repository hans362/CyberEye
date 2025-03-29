import uuid

from fastapi import APIRouter, Depends, Request
from sqlmodel import func, select

from db import SessionDep
from models.error import Error
from models.task import Task, TaskRead, TasksRead
from models.job import Job
from models.user import User

router = APIRouter(prefix="/tasks", tags=["tasks"])


@router.get("/", dependencies=[Depends(User.is_authenticated)])
def read_tasks(
    request: Request,
    session: SessionDep,
    offset: int = 0,
    limit: int = 100,
) -> TasksRead:
    q = select(Task, Job).join(Job)
    q_total = select(func.count(Task.id)).join(Job)
    try:
        User.is_admin(request, session)
    except Exception:
        q = q.where(Job.owner_id == uuid.UUID(request.session.get("uid")))
        q_total = q_total.where(Job.owner_id == uuid.UUID(request.session.get("uid")))
    q = q.order_by(Task.created_at.desc()).offset(offset).limit(limit)
    results = session.exec(q).all()
    return TasksRead(
        tasks=[TaskRead(**task.model_dump(), job=job) for task, job in results],
        total=session.exec(q_total).one(),
    )


@router.get("/{task_id}", dependencies=[Depends(User.is_authenticated)])
def read_task(
    request: Request, task_id: uuid.UUID, session: SessionDep
) -> TaskRead | Error:
    try:
        q = select(Task, Job).join(Job).where(Task.id == task_id)
        try:
            User.is_admin(request, session)
        except Exception:
            q = q.where(Job.owner_id == uuid.UUID(request.session.get("uid")))
        task, job = session.exec(q).first()
        if not task:
            return Error(message="测绘任务不存在")
        return TaskRead(**task.model_dump(), job=job)
    except Exception as e:
        return Error(message=str(e))
