
### 1. **XSS Attempt** (`<script>`)

curl -X POST http://localhost:8000/unknown -d '{"payload":"<script>alert(1)</script>"}'


### 2. **SQL Injection** (`OR 1=1`)

curl -X POST http://localhost:8000/login -d '{"user":"admin' OR '1'='1"}'

### 3. **Path Traversal** (`../../../../etc/passwd`)

curl -X GET "http://localhost:8000/files?path=../../../../etc/passwd"


### 4. **SSRF Attempt** (`127.0.0.1`)

curl -X POST http://localhost:8000/webhook -d '{"url":"http://127.0.0.1:8080/admin"}'

### 5. **Command Injection** (`; cat /etc/passwd`)

curl -X POST http://localhost:8000/exec -d '{"cmd":"; cat /etc/passwd"}'

### 6. **XXE Attempt** (`<!ENTITY`)

curl -X POST http://localhost:8000/upload -H "Content-Type: application/xml" -d '<?xml version="1.0"?><!DOCTYPE foo [<!ENTITY xxe SYSTEM "file:///etc/passwd">]><foo>&xxe;</foo>'

### 7. **JWT Tampering** (`alg=none`)

curl -H "Authorization: Bearer eyJhbGciOiJub25lIiwidHlwIjoiSldUIiwiY2VyIjoiMCJ9.eyJ1c2VyIjoiYWRtaW4ifQ." http://localhost:8000/api/profile

### 8. **Parameter Spam** (25+ params)

curl -X GET "http://localhost:8000/search?$(seq -s '&' 1 25 | sed 's/[0-9]*/param_&=value/g')"

### 9. **Payload Flooding** (6KB body)

curl -X POST http://localhost:8000/flood -d "$(python3 -c 'print("A"*6000)')"

### 10. **Script Flooding** (Repeated large JS)

PAYLOAD='{"data":"'"$(python3 -c "print('var x=1;' * 500)")"'"}'
curl -X POST http://localhost:8000/js -H "Content-Type: application/json" -d "$PAYLOAD"
curl -X POST http://localhost:8000/js -H "Content-Type: application/json" -d "$PAYLOAD"

### 11. **HTTP Header Injection** (`X-Forwarded-For: 127.0.0.1`)

curl -H "X-Forwarded-For: 127.0.0.1" http://localhost:8000/header-test

### 12. **Malformed JSON** (to test parser resilience)

curl -X POST http://localhost:8000/badjson -d '{ "key": "value", }'

### 13. **Obfuscated SQL** (`sel/**/ect`)

curl -X POST http://localhost:8000/query -d '{"q":"sel/**/ect * fr/**/om users"}'

### 14. **File Upload Abuse** (PDF signature)

curl -X POST http://localhost:8000/upload -d "$(python3 -c 'print("%PDF-1.7" + "A"*5000)')"

### 15. **Brute Force Simulation** (High request rate)

for i in {1..15}; do curl -s -o /dev/null -X POST http://localhost:8000/brute -d '{"id":"$i"}' & done; wait
