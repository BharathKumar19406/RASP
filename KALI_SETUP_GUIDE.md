# 🐉 RASP v2.0 - Complete Setup Guide for Kali Linux

**Runtime Application Self-Protection System**  
**Setup Date**: March 30, 2026 | **Version**: 2.0

---

## 📋 Table of Contents

1. [System Requirements](#system-requirements)
2. [Pre-Installation Steps](#pre-installation-steps)
3. [Step-by-Step Installation](#step-by-step-installation)
4. [Configuration](#configuration)
5. [Starting Services](#starting-services)
6. [Testing & Verification](#testing--verification)
7. [Dashboard Access](#dashboard-access)
8. [Troubleshooting](#troubleshooting)
9. [Docker Alternative](#docker-alternative)

---

## 🖥️ System Requirements

### Minimum Hardware
- **CPU**: 2+ cores
- **RAM**: 4GB minimum (8GB recommended)
- **Disk**: 2GB free space
- **OS**: Kali Linux 2024.x or newer

### Supported Kali Versions
- Kali Linux 2024.1 (Latest)
- Kali Linux 2023.4
- Kali Linux 2023.3
- Any Debian-based system

---

## 🔧 Pre-Installation Steps

### 1. Update System
```bash
sudo apt update && sudo apt upgrade -y
```

### 2. Install System Dependencies
```bash
# Python development tools
sudo apt install -y python3 python3-dev python3-pip python3-venv

# Build essentials (for compiling packages)
sudo apt install -y build-essential libssl-dev libffi-dev

# Redis server (optional but recommended)
sudo apt install -y redis-server

# Git (for cloning)
sudo apt install -y git

# Curl & wget
sudo apt install -y curl wget
```

### 3. Verify Python Installation
```bash
python3 --version  # Should be Python 3.8+
pip3 --version     # Should be pip 20.0+
```

---

## 📦 Step-by-Step Installation

### Step 1: Clone the Repository

```bash
# Option A: Using HTTPS (no SSH key needed)
git clone https://github.com/BharathKumar19406/RASP.git
cd RASP

# Option B: Using SSH (requires SSH key)
git clone git@github.com:BharathKumar19406/RASP.git
cd RASP
```

### Step 2: Create Python Virtual Environment

```bash
# Create venv
python3 -m venv rasp_env

# Activate venv
source rasp_env/bin/activate

# Verify activation (prompt should show (rasp_env))
which python3
```

### Step 3: Upgrade pip & setuptools

```bash
pip3 install --upgrade pip setuptools wheel
```

### Step 4: Install Python Dependencies

```bash
# Install all requirements
pip3 install -r requirements.txt

# Verify installation
pip3 list | grep -E "fastapi|uvicorn|streamlit|redis"
```

### Step 5: Create Required Directories

```bash
# Create logs directory
mkdir -p logs

# Create data directory
mkdir -p data

# Set permissions
chmod 755 logs data
```

### Step 6: Initialize Database

```bash
# Run initialization
python3 -c "from storage.db import init_db; init_db()"

# Verify database created
ls -lh rasp.db
```

---

## ⚙️ Configuration

### Step 1: Configure Environment Variables

```bash
# Create .env file
cat > .env << 'EOF'
# API Configuration
API_HOST=0.0.0.0
API_PORT=8000
DEBUG=False

# Database
DATABASE_URL=sqlite:///./rasp.db

# Redis Configuration
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0
REDIS_PASSWORD=

# Rate Limiting
RATE_LIMIT_ENABLED=True
DEFAULT_RATE_LIMIT=10  # requests per second
RATE_LIMIT_STRATEGY=token_bucket  # token_bucket|sliding_window|fixed_window|adaptive

# Security
SECRET_KEY=your-secret-key-here-change-in-production
ALLOWED_IPS=0.0.0.0

# Logging
LOG_LEVEL=INFO
LOG_FILE=logs/rasp.log

# Dashboard
DASHBOARD_PORT=8501
DASHBOARD_THEME=dark
EOF
```

### Step 2: Review Configuration

```bash
# Edit constants if needed
nano config/constants.py

# Key settings to check:
# - RATE_LIMIT_STRATEGIES
# - RISK_LEVELS
# - DETECTION_THRESHOLDS
```

### Step 3: Configure Thresholds

```bash
# Edit YAML config (optional)
nano config/thresholds.yaml

# Example thresholds:
# drift_threshold: 0.7
# anomaly_score: 0.65
# brute_force_limit: 5
```

---

## 🚀 Starting Services

### Option 1: Manual Start (Development)

#### Terminal 1 - Start API Server
```bash
# Activate venv
source rasp_env/bin/activate

# Start API
python3 run.py

# Expected output:
# Application startup complete
# Uvicorn running on http://0.0.0.0:8000
# Press CTRL+C to quit
```

#### Terminal 2 - Start Dashboard
```bash
# Activate venv
source rasp_env/bin/activate

# Start dashboard
streamlit run dashboard/dashboard.py --server.port=8501

# Expected output:
# You can now view your Streamlit app in your browser
# Local URL: http://localhost:8501
# Network URL: http://192.168.x.x:8501
```

### Option 2: Start with Background Services

```bash
# Start Redis (if not running)
sudo redis-server --daemonize yes

# Verify Redis
redis-cli ping  # Should return "PONG"

# Start API in background
source rasp_env/bin/activate && python3 run.py &

# Start Dashboard in background
source rasp_env/bin/activate && streamlit run dashboard/dashboard.py --server.port=8501 &

# View running processes
ps aux | grep -E "python|streamlit"
```

### Option 3: Using systemd (Production)

```bash
# Create systemd service file
sudo tee /etc/systemd/system/rasp.service > /dev/null << 'EOF'
[Unit]
Description=RASP v2.0 API Server
After=network.target redis-server.service

[Service]
Type=simple
User=$USER
WorkingDirectory=/path/to/RASP
Environment="PATH=/path/to/RASP/rasp_env/bin"
ExecStart=/path/to/RASP/rasp_env/bin/python3 run.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

# Replace '/path/to/RASP' with actual path:
# Example: /home/kali/RASP

# Enable and start service
sudo systemctl daemon-reload
sudo systemctl enable rasp.service
sudo systemctl start rasp.service

# Check status
sudo systemctl status rasp.service
```

---

## ✅ Testing & Verification

### 1. Check API Health
```bash
# Test API connectivity
curl -X GET http://localhost:8000/health

# Expected response:
# {"status":"operational","timestamp":"2026-03-30T12:00:00"}
```

### 2. Test Rate Limiting
```bash
# Send 15 rapid requests (limit is 10/sec)
for i in {1..15}; do 
  curl -X GET http://localhost:8000/api/users
  echo ""
done

# Expected: First 10 succeed, 11-15 get 429 (Too Many Requests)
```

### 3. Test Security Detection
```bash
# SQL Injection Detection
curl -X GET "http://localhost:8000/api/users?id=1' OR '1'='1"

# XSS Detection
curl -X POST "http://localhost:8000/api/submit" \
  -H "Content-Type: application/json" \
  -d '{"input":"<script>alert(1)</script>"}'

# Path Traversal Detection
curl -X GET "http://localhost:8000/api/file?path=../../etc/passwd"
```

### 4. View Application Logs
```bash
# Real-time logs
tail -f logs/rasp.log

# Filter for errors
grep "ERROR" logs/rasp.log

# Filter for attacks
grep "ATTACK" logs/rasp.log
```

### 5. Check Database
```bash
# Connect to SQLite database
sqlite3 rasp.db

# View tables
.tables

# Query events
SELECT * FROM events LIMIT 5;

# Exit
.exit
```

---

## 📊 Dashboard Access

### Access Points

```
🌐 API Server:        http://localhost:8000
   - Main API         http://localhost:8000/api/
   - Health Check     http://localhost:8000/health
   - Docs             http://localhost:8000/docs

📈 Dashboard:         http://localhost:8501
   - Main Dashboard   http://localhost:8501
   - Config Panel     Tab 2
   - Export Logs      Tab 3
   - Welcome          Tab 4

📱 From Other Machines:
   - Replace localhost with your IP
   - Example: http://192.168.1.100:8000
```

### Default Credentials
```
No authentication by default
Add auth in utils/auth.py if needed
```

---

## 🔍 Monitoring & Management

### View Running Services
```bash
# Check if services are running
ps aux | grep -E "python|streamlit"

# Monitor resource usage
top -p $(pgrep -f "python|streamlit" | tr '\n' ',')

# Check open ports
netstat -tlnp | grep -E "8000|8501|6379"
```

### Restart Services
```bash
# Stop all services
pkill -f "python run.py"
pkill -f "streamlit run"

# Or if using systemd
sudo systemctl stop rasp.service

# Start again
source rasp_env/bin/activate
python3 run.py &
streamlit run dashboard/dashboard.py &
```

### Clear Data
```bash
# Clear logs
rm logs/rasp.log

# Clear database
rm rasp.db

# Reinitialize
python3 -c "from storage.db import init_db; init_db()"
```

---

## 🚨 Troubleshooting

### Issue: "ModuleNotFoundError: No module named 'fastapi'"

**Solution:**
```bash
# Verify venv is activated
source rasp_env/bin/activate
which python3  # Should show path to rasp_env

# Reinstall dependencies
pip3 install -r requirements.txt --force-reinstall
```

### Issue: "Redis connection refused"

**Solution:**
```bash
# Start Redis
sudo redis-server

# Or restart if already running
sudo systemctl restart redis-server

# Verify Redis is running
redis-cli ping
```

### Issue: "Port 8000 already in use"

**Solution:**
```bash
# Find what's using port 8000
sudo lsof -i :8000

# Kill the process
sudo kill -9 <PID>

# Or use different port
python3 run.py --port 9000
```

### Issue: "Permission denied" errors

**Solution:**
```bash
# Fix directory permissions
chmod -R 755 logs data

# Run as current user (not root)
# Avoid using sudo for Python
```

### Issue: "Cannot connect to dashboard"

**Solution:**
```bash
# Verify streamlit is running
ps aux | grep streamlit

# Check if port 8501 is open
netstat -tlnp | grep 8501

# Try accessing from localhost first
# Then try from actual IP
```

### Issue: "Out of memory" errors

**Solution:**
```bash
# Reduce Redis memory
redis-cli CONFIG SET maxmemory 512mb

# Clear old data
redis-cli FLUSHDB

# Monitor memory usage
free -h
redis-cli INFO memory
```

---

## 🐳 Docker Alternative

### Option: Use Docker for Easy Setup

```bash
# Build Docker image
docker build -t rasp:2.0 .

# Run container
docker run -d \
  --name rasp \
  -p 8000:8000 \
  -p 8501:8501 \
  -v $(pwd)/logs:/app/logs \
  -v $(pwd)/data:/app/data \
  rasp:2.0

# Check logs
docker logs -f rasp

# Access services
# API:       http://localhost:8000
# Dashboard: http://localhost:8501
```

---

## 📝 Quick Reference Commands

```bash
# Activate environment
source rasp_env/bin/activate

# Start API
python3 run.py

# Start Dashboard
streamlit run dashboard/dashboard.py

# Check health
curl http://localhost:8000/health

# View logs
tail -f logs/rasp.log

# Test rate limiting
for i in {1..15}; do curl http://localhost:8000/api/users; done

# Stop all services
pkill -f "python run.py"
pkill -f "streamlit"

# Deactivate venv
deactivate
```

---

## 🎯 Next Steps

1. ✅ Complete installation above
2. ✅ Start services (dashboard + API)
3. ✅ Access http://localhost:8501 (dashboard)
4. ✅ Run tests from Testing section
5. ✅ Configure thresholds as needed
6. ✅ Deploy to production

---

## 📚 Additional Resources

- **Main Documentation**: [README.md](README.md)
- **Behavioral Detection**: [BEHAVIORAL_DETECTION_GUIDE.md](BEHAVIORAL_DETECTION_GUIDE.md)
- **Code Consolidation**: [CONSOLIDATION_SUMMARY.md](CONSOLIDATION_SUMMARY.md)
- **GitHub Repository**: [BharathKumar19406/RASP](https://github.com/BharathKumar19406/RASP)

---

**Setup Complete! 🎉**  
For issues, refer to troubleshooting section or check GitHub issues.
