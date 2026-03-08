import os
from dotenv import load_dotenv

load_dotenv()

class Settings:
    DB_URL = os.getenv("DB_URL")
    REDIS_URL = os.getenv("REDIS_URL")
    LOG_SECRET_KEY = os.getenv("LOG_SECRET_KEY", "default-secret")
    SAFE_MODE = os.getenv("SAFE_MODE", "false").lower() == "true"

settings = Settings()
