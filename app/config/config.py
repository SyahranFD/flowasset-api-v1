import os
from urllib.parse import quote_plus
from dotenv import load_dotenv, find_dotenv

load_dotenv(find_dotenv())

DB_USER = "postgres"
DB_PASS = quote_plus(os.getenv("DB_PASS", "admin"))
DB_NAME = os.getenv("DB_NAME", "fastapi_flowasset_api")
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "5432")
TEST_DB_NAME = os.getenv("TEST_DB_NAME", "test_db")

DB_POOLSIZE = 50
DB_MAXOVERFLOW = 25
DB_POOLTIMEOUT = 30
DB_POOLRECYCLE = 1800

SECRET_KEY = os.getenv("SECRET_KEY", "change_me_in_env")
JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
JWT_ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("JWT_ACCESS_TOKEN_EXPIRE_MINUTES", "60"))
JWT_REFRESH_TOKEN_EXPIRE_DAYS = int(os.getenv("JWT_REFRESH_TOKEN_EXPIRE_DAYS", "7"))
APP_NAME = os.getenv("APP_NAME", "FlowAsset API")
