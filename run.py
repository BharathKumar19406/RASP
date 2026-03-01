import subprocess
import sys
import time
import os
from dotenv import load_dotenv

# ✅ Load .env BEFORE anything else
load_dotenv()  # ← Critical!

def main():
    required = ["DB_URL", "REDIS_URL", "LOG_SECRET_KEY"]
    for var in required:
        if not os.getenv(var):
            print(f"❌ Missing .env variable: {var}")
            sys.exit(1)

    api = subprocess.Popen([
        sys.executable, "-m", "uvicorn",
        "app.main:app", "--host", "0.0.0.0", "--port", "8000"
    ])
    
    time.sleep(2)
    
    dashboard = subprocess.Popen([
        sys.executable, "-m", "streamlit",
        "run", "dashboard/config_pane.py", "--server.port=8501"
    ])
    
    print("✅ Application: http://localhost:8000")
    print("✅ Admin Dashboard: http://localhost:8501")
    print("\nPress Ctrl+C to stop.\n")

    try:
        api.wait()
    except KeyboardInterrupt:
        print("\n🛑 Shutting down...")
        api.terminate()
        dashboard.terminate()
        api.wait()
        dashboard.wait()
        print("✅ Shutdown complete.")

if __name__ == "__main__":
    main()
