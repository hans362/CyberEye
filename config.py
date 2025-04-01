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

PORT_SCAN_RANGE = [
    21,
    22,
    80,
    81,
    135,
    139,
    443,
    445,
    1433,
    1521,
    3306,
    5432,
    6379,
    7001,
    8000,
    8080,
    8089,
    9000,
    9200,
    11211,
    27017,
]
PORT_SCAN_TIMEOUT = 1

SCHEDULER_INTERVAL = 5
WORKER_INTERVAL = 1
