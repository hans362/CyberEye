import json
from time import sleep

from sqlmodel import select, update

from db import Session, engine
from models.job import Job
from models.report import IPAddr, Service, SubDomain, SubDomainIPAddr
from models.task import Task

SCHEDULER_INTERVAL = 5


# 对于待启动的测绘项目，自动启动测绘项目，创建子域名收集任务
def enter_subdomain_collect_stage():
    session = Session(engine)
    pending_jobs = session.exec(select(Job).where(Job.status == "pending")).all()
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
        except Exception as e:
            session.rollback()
            job.status = "failed"
            job.message = str(e)
            session.add(job)
            session.commit()
            session.refresh(job)
    session.close()


# 对于正在运行的测绘项目，如果子域名收集任务已经完成且没有IP解析任务，自动创建IP解析任务
def enter_ip_resolve_stage():
    session = Session(engine)
    running_jobs = session.exec(select(Job).where(Job.status == "running")).all()
    for job in running_jobs:
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
                        )
                        for subdomain in subdomains
                    ]
                )
            session.commit()
        except Exception as e:
            session.rollback()
            job.status = "failed"
            job.message = str(e)
            session.add(job)
            session.commit()
            session.refresh(job)
            continue
        try:
            subdomains = session.exec(
                select(SubDomain).where(SubDomain.job_id == job.id)
            ).all()
            if len(subdomains) == 0:
                job.status = "completed"
                session.add(job)
                session.commit()
                session.refresh(job)
                continue
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
            session.rollback()
            job.status = "failed"
            job.message = str(e)
            session.add(job)
            session.commit()
            session.refresh(job)
    session.close()


# 对于正在运行的测绘项目，如果IP解析任务已经完成且没有端口扫描任务，自动创建端口扫描任务
def enter_port_scan_stage():
    session = Session(engine)
    running_jobs = session.exec(select(Job).where(Job.status == "running")).all()
    for job in running_jobs:
        q = select(Task)
        q = q.where(Task.job_id == job.id)
        q = q.where(Task.method_name == "ip_resolve")
        q = q.where(Task.status != "completed")
        if session.exec(q).first():
            continue
        q = select(Task)
        q = q.where(Task.job_id == job.id)
        q = q.where(Task.method_name == "port_scan")
        if session.exec(q).first():
            continue
        q = select(Task)
        q = q.where(Task.job_id == job.id)
        q = q.where(Task.method_name == "ip_resolve")
        ip_tasks = session.exec(q).all()
        if len(ip_tasks) == 0:
            continue
        try:
            ips = set()
            for task in ip_tasks:
                ips.update(json.loads(task.output))
            if len(ips) == 0:
                job.status = "completed"
                session.add(job)
                session.commit()
                session.refresh(job)
                continue
            session.add_all(
                [
                    IPAddr(
                        ip=ip,
                        job_id=job.id,
                    )
                    for ip in ips
                ]
            )
            for task in ip_tasks:
                subdomain_id = session.exec(
                    select(SubDomain.id)
                    .where(SubDomain.domain == json.loads(task.input)["domain"])
                    .where(SubDomain.job_id == job.id)
                ).first()
                session.add_all(
                    [
                        SubDomainIPAddr(
                            subdomain_id=subdomain_id,
                            ip_id=ip_id,
                        )
                        for ip_id in session.exec(
                            select(IPAddr.id).where(IPAddr.job_id == job.id)
                        ).all()
                    ]
                )
            session.commit()
        except Exception as e:
            session.rollback()
            job.status = "failed"
            job.message = str(e)
            session.add(job)
            session.commit()
            session.refresh(job)
            continue
        try:
            ips = session.exec(select(IPAddr).where(IPAddr.job_id == job.id)).all()
            session.add_all(
                [
                    Task(
                        name=f"port_scan_{ip.ip}",
                        method_name="port_scan",
                        input=json.dumps({"ip": ip.ip}),
                        output="",
                        status="pending",
                        job_id=job.id,
                    )
                    for ip in ips
                ]
            )
            session.commit()
        except Exception as e:
            session.rollback()
            job.status = "failed"
            job.message = str(e)
            session.add(job)
            session.commit()
            session.refresh(job)
    session.close()


# 对于正在运行的测绘项目，如果端口扫描任务已经完成且没有服务扫描任务，自动创建服务扫描任务
def enter_service_scan_stage():
    session = Session(engine)
    running_jobs = session.exec(select(Job).where(Job.status == "running")).all()
    for job in running_jobs:
        q = select(Task)
        q = q.where(Task.job_id == job.id)
        q = q.where(Task.method_name == "port_scan")
        q = q.where(Task.status != "completed")
        if session.exec(q).first():
            continue
        q = select(Task)
        q = q.where(Task.job_id == job.id)
        q = q.where(Task.method_name == "service_scan")
        if session.exec(q).first():
            continue
        q = select(Task)
        q = q.where(Task.job_id == job.id)
        q = q.where(Task.method_name == "port_scan")
        port_tasks = session.exec(q).all()
        if len(port_tasks) == 0:
            continue
        try:
            for task in port_tasks:
                ports = json.loads(task.output)
                ip = session.exec(
                    select(IPAddr)
                    .where(
                        IPAddr.ip == json.loads(task.input)["ip"],
                    )
                    .where(IPAddr.job_id == job.id)
                ).first()
                ip.ports = ",".join([str(port) for port in ports if port])
                session.add(ip)
            session.commit()
        except Exception as e:
            session.rollback()
            job.status = "failed"
            job.message = str(e)
            session.add(job)
            session.commit()
            session.refresh(job)
            continue
        try:
            ips = session.exec(select(IPAddr).where(IPAddr.job_id == job.id)).all()
            session.add_all(
                [
                    Task(
                        name=f"service_scan_{ip.ip}",
                        method_name="service_scan",
                        input=json.dumps(
                            {
                                "ip": ip.ip,
                                "ports": [
                                    int(port) for port in ip.ports.split(",") if port
                                ],
                            }
                        ),
                        output="",
                        status="pending",
                        job_id=job.id,
                    )
                    for ip in ips
                ]
            )
            session.commit()
        except Exception as e:
            session.rollback()
            job.status = "failed"
            job.message = str(e)
            session.add(job)
            session.commit()
            session.refresh(job)
    session.close()


# 对于正在运行的测绘项目，如果服务扫描任务已经完成，自动结束测绘项目
def enter_end_stage():
    session = Session(engine)
    running_jobs = session.exec(select(Job).where(Job.status == "running")).all()
    for job in running_jobs:
        q = select(Task)
        q = q.where(Task.job_id == job.id)
        q = q.where(Task.method_name == "service_scan")
        q = q.where(Task.status != "completed")
        if session.exec(q).first():
            continue
        q = select(Task)
        q = q.where(Task.job_id == job.id)
        q = q.where(Task.method_name == "service_scan")
        service_tasks = session.exec(q).all()
        if len(service_tasks) == 0:
            continue
        try:
            for task in service_tasks:
                services = json.loads(task.output)
                ip = session.exec(
                    select(IPAddr)
                    .where(
                        IPAddr.ip == json.loads(task.input)["ip"],
                    )
                    .where(IPAddr.job_id == job.id)
                ).first()
                session.add_all(
                    [
                        Service(
                            port=service["port"],
                            banner=service["banner"],
                            protocol=service["protocol"],
                            ip_id=ip.id,
                        )
                        for service in services
                    ]
                )
            session.commit()
        except Exception as e:
            session.rollback()
            job.status = "failed"
            job.message = str(e)
            session.add(job)
            session.commit()
            session.refresh(job)
            continue
        job.status = "completed"
        session.add(job)
        session.commit()
        session.refresh(job)
    session.close()


def mark_failed_jobs():
    session = Session(engine)
    failed_jobs_ids = session.exec(
        select(Task.job_id).where(Task.status == "failed")
    ).all()
    session.exec(
        update(Job)
        .where(Job.id.in_(failed_jobs_ids))
        .values(status="failed", message="一个或多个测绘任务失败")
    )
    session.commit()
    session.close()


while True:
    mark_failed_jobs()
    enter_subdomain_collect_stage()
    enter_ip_resolve_stage()
    enter_port_scan_stage()
    enter_service_scan_stage()
    enter_end_stage()
    sleep(SCHEDULER_INTERVAL)
