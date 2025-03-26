import json
from tasks.domain import subdomain_collect, ip_resolve
from tasks.port import port_scan
from models.task import Task
from db import Session, engine
from sqlmodel import select, text
import os

session = Session(engine)

nonce = os.urandom(32).hex()
# update tasks set status='running', nonce=nonce where status='pending' limit 1
session.execute(
    text(
        "update task set status='running', nonce=:nonce where status='pending' limit 1;"
    ),
    {"nonce": nonce},
)
session.commit()
task = session.exec(select(Task).where(Task.nonce == nonce)).first()
if task:
    func = globals()[task.method_name]
    output = func(**json.loads(task.input))
    task.output = json.dumps(output)
    task.status = "completed"
    session.add(task)
    session.commit()
    session.refresh(task)
