import json
from uuid import uuid4
from sqlmodel import select
from models.job import Job
from models.report import SubDomain
from models.task import Task
from db import Session, engine
from time import sleep


# start job, collect subdomain
def enter_subdomain_collect_stage():
    session = Session(engine)
    pending_jobs = session.exec(select(Job).where(Job.status == "pending")).all()
    print(pending_jobs)
    for job in pending_jobs:
        try:
            job.status = "running"
            session.add(job)
            task = Task(
                name=f"subdomain_collect_{job.domain}",
                method_name="subdomain_collect",
                input=json.dumps({"domain": job.domain}),
                output="",
                status="pending",
                job_id=job.id,
            )
            session.add(task)
            session.commit()
            session.refresh(job)
        except Exception:
            session.rollback()
            job.status = "failed"
            session.add(job)
            session.commit()
            session.refresh(job)
    session.close()


def enter_ip_resolve_stage():
    session = Session(engine)
    running_jobs = session.exec(select(Job).where(Job.status == "running")).all()
    print(running_jobs)
    for job in running_jobs:
        # subdomain tasks all completed and no ip tasks
        q = select(Task)
        q = q.where(Task.job_id == job.id)
        q = q.where(Task.method_name == "subdomain_collect")
        q = q.where(Task.status != "completed")
        if session.exec(q).first():
            continue
        q = select(Task)
        q = q.where(Task.job_id == job.id)
        q = q.where(Task.method_name == "ip_resolve")
        if session.exec(q).first():
            continue
        # save completed subdomain tasks to report
        q = select(Task)
        q = q.where(Task.job_id == job.id)
        q = q.where(Task.method_name == "subdomain_collect")
        subdomain_tasks = session.exec(q).all()
        try:
            for task in subdomain_tasks:
                subdomains = json.loads(task.output)
                session.add_all(
                    [
                        SubDomain(
                            domain=subdomain,
                            job_id=job.id,
                            id=str(uuid4()),
                        )
                        for subdomain in subdomains
                    ]
                )
            session.commit()
        except Exception as e:
            session.rollback()
            job.status = "failed"
            session.add(job)
            session.commit()
            session.refresh(job)
            print(e)
            continue
        # create ip resolve tasks
        try:
            subdomains = session.exec(
                select(SubDomain).where(SubDomain.job_id == job.id)
            ).all()
            session.add_all(
                [
                    Task(
                        name=f"ip_resolve_{subdomain.domain}",
                        method_name="ip_resolve",
                        input=json.dumps({"domain": subdomain.domain}),
                        output="",
                        status="pending",
                        job_id=job.id,
                    )
                    for subdomain in subdomains
                ]
            )
            session.commit()
        except Exception as e:
            print(e)
            session.rollback()
            job.status = "failed"
            session.add(job)
            session.commit()
            session.refresh(job)
    session.close()


while True:
    enter_subdomain_collect_stage()
    enter_ip_resolve_stage()
    sleep(5)
