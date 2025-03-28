import json
import os
from time import sleep

from sqlmodel import select, text

from db import Session, engine
from models import *
from tasks.domain import ip_resolve, subdomain_collect
from tasks.port import port_scan
from tasks.service import service_scan

WORKER_INTERVAL = 1

funcs = {
    "ip_resolve": ip_resolve,
    "subdomain_collect": subdomain_collect,
    "port_scan": port_scan,
    "service_scan": service_scan,
}

while True:
    session = Session(engine)
    nonce = os.urandom(32).hex()
    session.execute(
        text(
            "UPDATE task SET status='running', nonce=:nonce WHERE status='pending' LIMIT 1;"
        ),
        {"nonce": nonce},
    )
    session.commit()
    task = session.exec(select(Task).where(Task.nonce == nonce)).first()
    if task:
        try:
            func = funcs[task.method_name]
            output = func(**json.loads(task.input))
            task.output = json.dumps(output)
            task.status = "completed"
            session.add(task)
            session.commit()
            session.refresh(task)
        except Exception as e:
            session.rollback()
            task.status = "failed"
            task.message = str(e)
            session.add(task)
            session.commit()
            session.refresh(task)
    session.close()
    sleep(WORKER_INTERVAL)
