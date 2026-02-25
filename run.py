import subprocess
import sys
import time
import os

def main():
    print("🚀 Starting RASP Security System...\n")
    
    # Ensure config directory exists
    os.makedirs("config", exist_ok=True)
    
    # Start FastAPI
    api_proc = subprocess.Popen([
        sys.executable, "-m", "uvicorn",
        "app.main:app",
        "--host", "0.0.0.0",
        "--port", "8000"
    ])
    
    time.sleep(2)
    
    # Start Streamlit Dashboard
    dash_proc = subprocess.Popen([
        sys.executable, "-m", "streamlit",
        "run", "dashboard/streamlit_app.py",
        "--server.port=8501"
    ])
    
    print("✅ Application: http://localhost:8000")
    print("✅ Admin Dashboard: http://localhost:8501\n")
    print("Press Ctrl+C to stop.\n")
    
    try:
        api_proc.wait()
    except KeyboardInterrupt:
        print("\n🛑 Shutting down services...")
        api_proc.terminate()
        dash_proc.terminate()
        api_proc.wait()
        dash_proc.wait()
        print("✅ Shutdown complete.")

if __name__ == "__main__":
    main()
