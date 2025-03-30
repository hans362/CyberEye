import os
from dotenv import load_dotenv

load_dotenv()

DATABASE_HOST = os.environ.get("DATABASE_HOST", "localhost")
DATABASE_PORT = os.environ.get("DATABASE_PORT", 3306)
DATABASE_USER = os.environ.get("DATABASE_USER", "root")
DATABASE_PASSWORD = os.environ.get("DATABASE_PASSWORD", "root")
DATABASE_NAME = os.environ.get("DATABASE_NAME", "cybereye")
DATABASE_URL = f"mysql+pymysql://{DATABASE_USER}:{DATABASE_PASSWORD}@{DATABASE_HOST}:{DATABASE_PORT}/{DATABASE_NAME}?charset=utf8mb4"

GEOIP_DATABASES_AUTO_UPDATE = False

SCHEDULER_INTERVAL = 5
WORKER_INTERVAL = 1
