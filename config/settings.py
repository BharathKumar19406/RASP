import os
from dotenv import load_dotenv
import yaml

load_dotenv()

class Settings:
    DB_URL = os.getenv("DB_URL")
    REDIS_URL = os.getenv("REDIS_URL")
    APP_HOST = os.getenv("APP_HOST", "0.0.0.0")
    APP_PORT = int(os.getenv("APP_PORT", 8000))
    DASHBOARD_PORT = int(os.getenv("DASHBOARD_PORT", 8501))
    SAFE_MODE = os.getenv("SAFE_MODE", "false").lower() == "true"  # ← NEW

    @staticmethod
    def load_thresholds():
        with open("config/thresholds.yaml") as f:
            return yaml.safe_load(f)

    @staticmethod
    def load_sensitive_endpoints():
        with open("config/sensitive_endpoints.yaml") as f:
            return yaml.safe_load(f)

settings = Settings()
thresholds = settings.load_thresholds()
sensitive_endpoints = settings.load_sensitive_endpoints()
