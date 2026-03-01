# config/settings.py
import os
import yaml
from dotenv import load_dotenv

load_dotenv()

class Settings:
    DB_URL = os.getenv("DB_URL")
    REDIS_URL = os.getenv("REDIS_URL")
    LOG_SECRET_KEY = os.getenv("LOG_SECRET_KEY", "default-secret")
    SAFE_MODE = os.getenv("SAFE_MODE", "false").lower() == "true"

    @property
    def thresholds(self):
        try:
            with open("config/thresholds.yaml") as f:
                cfg = yaml.safe_load(f)
            return cfg.get("drift", {"medium": 15, "high": 30})
        except Exception:
            return {"medium": 15, "high": 30}

settings = Settings()
