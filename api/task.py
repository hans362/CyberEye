import uuid

from fastapi import APIRouter

from db import SessionDep
from models.error import Error
from models.task import Task, TaskRead

router = APIRouter(prefix="/tasks", tags=["tasks"])


@router.get("/{task_id}")
def read_task(task_id: uuid.UUID, session: SessionDep) -> TaskRead | Error:
    try:
        task = session.get(Task, task_id)
        if not task:
            return Error(message="测绘任务不存在")
        return task
    except Exception as e:
        return Error(message=str(e))
