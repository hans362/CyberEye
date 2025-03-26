from fastapi import FastAPI
from db import create_db_and_tables
from api.user import router as user_router
from api.job import router as job_router

app = FastAPI()


@app.on_event("startup")
def on_startup():
    create_db_and_tables()


app.include_router(user_router)
app.include_router(job_router)
