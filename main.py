import os

from fastapi import FastAPI, Request
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.middleware.sessions import SessionMiddleware

from api.job import router as job_router
from api.task import router as task_router
from api.user import router as user_router
from db import SessionDep, create_db_and_tables
from models.user import User

if not os.path.exists(os.path.join(os.getcwd(), "data")):
    os.makedirs(os.path.join(os.getcwd(), "data"))

if not os.path.exists("data/.secretkey"):
    open("data/.secretkey", "wb").write(os.urandom(32))

app = FastAPI()
app.add_middleware(
    SessionMiddleware,
    secret_key=open("data/.secretkey", "rb").read(),
    max_age=24 * 60 * 60,
)

app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")


@app.on_event("startup")
def on_startup():
    create_db_and_tables()


api = FastAPI()
api.include_router(user_router)
api.include_router(job_router)
api.include_router(task_router)
app.mount("/api", api)


@app.get("/")
def index(request: Request, session: SessionDep):
    try:
        user = User.is_authenticated(request, session)
        return templates.TemplateResponse(
            "index.html", {"request": request, "user": user}
        )
    except Exception:
        return RedirectResponse("/login")


@app.get("/login")
def login(request: Request, session: SessionDep):
    try:
        User.is_authenticated(request, session)
        return RedirectResponse("/")
    except Exception:
        return templates.TemplateResponse("login.html", {"request": request})


@app.get("/jobs")
def jobs(request: Request, session: SessionDep):
    try:
        user = User.is_authenticated(request, session)
        return templates.TemplateResponse(
            "jobs.html", {"request": request, "user": user}
        )
    except Exception:
        return RedirectResponse("/login")


@app.get("/job/{job_id}")
def job(request: Request, job_id: str, session: SessionDep):
    try:
        user = User.is_authenticated(request, session)
        return templates.TemplateResponse(
            "job.html", {"request": request, "user": user, "job_id": job_id}
        )
    except Exception:
        return RedirectResponse("/login")


@app.get("/tasks")
def tasks(request: Request, session: SessionDep):
    try:
        user = User.is_authenticated(request, session)
        return templates.TemplateResponse(
            "tasks.html", {"request": request, "user": user}
        )
    except Exception:
        return RedirectResponse("/login")


@app.get("/users")
def users(request: Request, session: SessionDep):
    try:
        user = User.is_authenticated(request, session)
        return templates.TemplateResponse(
            "users.html", {"request": request, "user": user}
        )
    except Exception:
        return RedirectResponse("/login")
