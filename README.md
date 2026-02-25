# RASP Security System – Behavior Drift Detection

# 🛡️ RASP with Behavior Drift Detection  
**Runtime Application Self-Protection (RASP) system that detects and blocks attacks using lightweight behavioral analysis — no heavy ML required.**


## 🎯 Project Overview

This project implements a **Runtime Application Self-Protection (RASP)** system that embeds directly into your application to monitor, learn, and respond to anomalous behavior in real-time. Unlike traditional security tools that operate at the network layer, RASP understands your application's logic and can detect unknown attacks like:

- **Payload Flooding**: Abnormally large request bodies
- **Parameter Spam**: Excessive query parameters  
- **Behavioral Anomalies**: Unusual API call sequences
- **Business Logic Abuse**: Legitimate requests used maliciously

**Key Innovation**: Uses **lightweight statistical profiling** instead of heavy machine learning, making it perfect for academic projects while maintaining enterprise-grade capabilities.

---

## ✨ Key Features

### 🔒 Security Features
- **Real-time Attack Detection**: Monitors every request for behavioral anomalies
- **Attack Classification**: Labels attacks as "Payload Flooding", "Parameter Spam", etc.
- **Automatic Mitigation**: Blocks high-risk requests with HTTP 403
- **IP Blacklisting**: Temporarily blocks malicious IPs (5 minutes)
- **Immutable Audit Logs**: Cryptographically sealed logs for compliance
- **Privacy-Preserving**: Never stores sensitive data (passwords, tokens, PII)

### 📊 Observability Features
- **Real-time Dashboard**: Streamlit UI with live visualizations
- **Risk Distribution**: Histogram of LOW/MEDIUM/HIGH risk events
- **Attack Types**: Pie chart showing attack classifications
- **Drift Timeline**: Line chart showing drift scores over time
- **Event Log**: Detailed table with full context

### ⚙️ Developer Features
- **Safe Mode**: Disable blocking during development/testing
- **One-Command Deployment**: `python run.py` starts everything
- **Configurable Thresholds**: Adjust sensitivity via YAML files
- **Performance Optimized**: <10% latency overhead
- **Fail-Open Design**: Never crashes your application

---

## 🖥️ System Requirements


### Software Requirements
| Component | Version | Installation Method |
|-----------|---------|-------------------|
| **Operating System** | Linux/Windows/macOS | - |
| **Python** | 3.9+ | [python.org](https://www.python.org/downloads/) |
| **PostgreSQL** | 12+ | Package manager or Docker |
| **Redis** | 6.0+ | Package manager or Docker |

---

## 🚀 Installation

### Step 1: Install Prerequisites

#### **Option A: Using Docker (Recommended for Kali Linux)**
```bash
# Install Docker if not already installed
sudo apt update
sudo apt install docker.io
sudo systemctl start docker
sudo usermod -aG docker $USER
# Log out and back in for group changes to take effect

# Start PostgreSQL container
docker run -d --name rasp-postgres \
  -e POSTGRES_PASSWORD=password \
  -e POSTGRES_DB=rasp_db \
  -p 5432:5432 \
  postgres:15

# Start Redis container
docker run -d --name rasp-redis -p 6379:6379 redis:7
```

#### **Option B: Install Natively on Kali Linux**
```bash
# Update package list
sudo apt update

# Install PostgreSQL
sudo apt install postgresql postgresql-contrib
sudo systemctl start postgresql
sudo -u postgres psql -c "CREATE DATABASE rasp_db;"
sudo -u postgres psql -c "ALTER USER postgres PASSWORD 'password';"

# Install Redis
sudo apt install redis-server
sudo systemctl start redis-server
```

> 💡 **Note for Kali Linux**: You may see collation warnings with PostgreSQL. These are harmless for this project and can be ignored.

### Step 2: Set Up the Project

```bash
# Clone or create project directory
mkdir ~/Desktop/rasp-security-system && cd ~/Desktop/rasp-security-system

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install Python dependencies
pip install --upgrade pip
pip install fastapi uvicorn[standard] sqlalchemy psycopg2-binary redis pyyaml python-dotenv streamlit plotly pandas pyjwt cryptography pytest requests
```

### Step 3: Configure Environment

Create `.env` file in your project root:
```env
DB_URL=postgresql://postgres:password@localhost:5432/rasp_db
REDIS_URL=redis://localhost:6379/0
LOG_SECRET_KEY=my-secret-key-for-cryptographic-logging
SAFE_MODE=false
```

Create configuration directory and files:
```bash
mkdir config
```

**`config/thresholds.yaml`**:
```yaml
drift:
  medium: 60
  high: 85
```

**`config/sensitive_endpoints.yaml`**:
```yaml
high_risk:
  - /api/transfer
  - /api/delete-account
  - /admin/reset-password
```

### Step 4: Initialize Database

If you're using the enhanced version with immutable logs, create the database tables:
```bash
# This is handled automatically by SQLAlchemy in the code
# But you can verify the connection:
python3 -c "from storage.db import engine; print('Database connected successfully!')"
```

---



### Security Thresholds (`config/thresholds.yaml`)
- **Medium Risk**: Drift score ≥ 60 → Rate limiting applied
- **High Risk**: Drift score ≥ 85 → Request blocked



## ▶️ Usage

### Start the System

source venv/bin/activate

# Run the system
python run.py
```

You'll see:
```
🚀 Starting RASP Security System...

✅ Application: http://localhost:8000
✅ Admin Dashboard: http://localhost:8501

Press Ctrl+C to stop.
```

### Access Endpoints
- **Protected Application**: `http://localhost:8000`
- **Admin Dashboard**: `http://localhost:8501`
- **Health Check**: `http://localhost:8000/health`

### Test Endpoints
Your protected application includes these test endpoints:
- `POST /api/login` - User login
- `POST /api/transfer` - Fund transfer (sensitive endpoint)
- `DELETE /api/delete-account` - Account deletion (sensitive endpoint)

---

## 🎥 Demo Script

Save this as `demo.sh` in your project root:

```bash
#!/bin/bash
echo "🎯 RASP Security System - Live Demo"
echo "=================================="

# Build baseline with normal traffic
echo "1. Building baseline with normal traffic..."
for i in {1..5}; do
    curl -s -X POST http://localhost:8000/api/transfer \
      -H "Content-Type: application/json" \
      -d '{"to":"friend","amount":10}' > /dev/null
done
echo "✅ Baseline established."

# Wait for baseline to settle
sleep 3

# Launch payload flooding attack
echo "2. Launching Payload Flooding attack..."
RESPONSE=$(curl -s -w "%{http_code}" -X POST http://localhost:8000/api/transfer \
  -H "Content-Type: application/json" \
  -d '{"to":"hacker","amount":99999,"note":"'$(python3 -c "print('A'*6000)")'"}')

HTTP_CODE="${RESPONSE: -3}"
if [ "$HTTP_CODE" = "403" ]; then
    echo "✅ ATTACK BLOCKED! (HTTP 403)"
else
    echo "❌ Attack not blocked (HTTP $HTTP_CODE)"
fi

echo "3. Check dashboard at http://localhost:8501 for real-time logs."
echo "4. Refresh the dashboard to see the HIGH-risk event!"
```

Make it executable and run:
```bash
chmod +x demo.sh
./demo.sh
```


### Verification Commands
```bash
# Check Redis status
redis-cli PING

# Check PostgreSQL connection
psql -h localhost -U postgres -d rasp_db -c "SELECT version();"

# Test API health
curl http://localhost:8000/health

# View Python packages
pip list | grep -E "(fastapi|redis|psycopg2)"
```

---


### Learning Outcomes
- Runtime application security
- Behavioral anomaly detection
- Threat intelligence integration
- Secure logging and auditing

