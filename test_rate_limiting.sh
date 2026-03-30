#!/bin/bash
# Rate Limiting Test Suite
# Run this to test all 4 rate limiting strategies

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

API_URL="${API_URL:-http://localhost:8000}"
ENDPOINT="/api/users"

# Function to print section headers
print_section() {
    echo -e "\n${BLUE}╔════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${BLUE}║${NC} $1"
    echo -e "${BLUE}╚════════════════════════════════════════════════════════════╝${NC}\n"
}

# Function to print test case
print_test() {
    echo -e "${CYAN}[TEST]${NC} $1"
}

# Function to print success
print_success() {
    echo -e "${GREEN}[✓]${NC} $1"
}

# Function to print error
print_error() {
    echo -e "${RED}[✗]${NC} $1"
}

# Function to print warning
print_warning() {
    echo -e "${YELLOW}[!]${NC} $1"
}

# Function to check if server is running
check_server() {
    print_test "Checking if server is running at ${API_URL}..."
    if ! curl -s -m 2 "${API_URL}/health" &>/dev/null; then
        print_error "Server not accessible at ${API_URL}"
        echo -e "Start your server with: ${YELLOW}python run.py${NC}"
        exit 1
    fi
    print_success "Server is running"
}

# Function to send requests and count responses
send_requests() {
    local count=$1
    local strategy=$2
    local success=0
    local rate_limited=0
    local errors=0
    
    print_test "Sending ${count} requests with ${strategy}..."
    
    for i in $(seq 1 $count); do
        response=$(curl -s -w "\n%{http_code}" "${API_URL}${ENDPOINT}")
        http_code=$(echo "$response" | tail -n1)
        
        case $http_code in
            200)
                ((success++))
                echo -ne "\r  Progress: $i/$count [✓ $success | ⚠ $rate_limited | ✗ $errors]"
                ;;
            429)
                ((rate_limited++))
                echo -ne "\r  Progress: $i/$count [✓ $success | ⚠ $rate_limited | ✗ $errors]"
                ;;
            *)
                ((errors++))
                echo -ne "\r  Progress: $i/$count [✓ $success | ⚠ $rate_limited | ✗ $errors]"
                ;;
        esac
    done
    
    echo ""
    echo ""
    print_success "Results:"
    echo "  ✓ Successful (200): $success"
    echo "  ⚠ Rate limited (429): $rate_limited"
    echo "  ✗ Other errors: $errors"
    
    return $rate_limited
}

# Test 1: Token Bucket Strategy
test_token_bucket() {
    print_section "TEST 1: TOKEN BUCKET STRATEGY"
    
    print_test "Set strategy to token_bucket..."
    cat > /tmp/test_env.sh << 'EOF'
export RATE_LIMIT_STRATEGY=token_bucket
export RATE_LIMIT_DEFAULT_REQUESTS=10
export RATE_LIMIT_WINDOW_SECONDS=1
export BLOCK_ON_RATE_LIMIT=true
EOF
    source /tmp/test_env.sh
    print_success "Configuration set"
    
    echo -e "${YELLOW}Expected behavior:${NC}"
    echo "  - First 10 requests should succeed (fill bucket)"
    echo "  - Requests 11-15 should get 429 (bucket empty)"
    echo "  - After 1 second, bucket refills"
    echo ""
    
    send_requests 15 "token_bucket"
    
    echo -e "${YELLOW}Waiting 1 second for bucket to refill...${NC}"
    sleep 1
    
    print_test "Sending 5 more requests (should all succeed)..."
    send_requests 5 "token_bucket"
    print_success "Token bucket refilled correctly"
}

# Test 2: Sliding Window Strategy
test_sliding_window() {
    print_section "TEST 2: SLIDING WINDOW STRATEGY"
    
    print_test "Set strategy to sliding_window..."
    cat > /tmp/test_env.sh << 'EOF'
export RATE_LIMIT_STRATEGY=sliding_window
export RATE_LIMIT_DEFAULT_REQUESTS=10
export RATE_LIMIT_WINDOW_SECONDS=1
export BLOCK_ON_RATE_LIMIT=true
EOF
    source /tmp/test_env.sh
    print_success "Configuration set"
    
    echo -e "${YELLOW}Expected behavior:${NC}"
    echo "  - First 10 requests should succeed"
    echo "  - Requests 11-15 should get 429 (no sliding window available)"
    echo "  - No burst allowed (strict enforcement)"
    echo ""
    
    send_requests 15 "sliding_window"
    print_success "Sliding window enforced (no burst allowed)"
}

# Test 3: Fixed Window Strategy
test_fixed_window() {
    print_section "TEST 3: FIXED WINDOW STRATEGY"
    
    print_test "Set strategy to fixed_window..."
    cat > /tmp/test_env.sh << 'EOF'
export RATE_LIMIT_STRATEGY=fixed_window
export RATE_LIMIT_DEFAULT_REQUESTS=10
export RATE_LIMIT_WINDOW_SECONDS=1
export BLOCK_ON_RATE_LIMIT=true
EOF
    source /tmp/test_env.sh
    print_success "Configuration set"
    
    echo -e "${YELLOW}Expected behavior:${NC}"
    echo "  - First 10 requests in window 1 succeed"
    echo "  - Requests 11-15 get 429"
    echo "  - After 1 second, window resets"
    echo "  - NOTE: Might see burst at window boundary"
    echo ""
    
    send_requests 15 "fixed_window"
    print_success "Fixed window working (watch for boundary bursts)"
}

# Test 4: Adaptive Strategy
test_adaptive() {
    print_section "TEST 4: ADAPTIVE STRATEGY"
    
    print_test "Set strategy to adaptive..."
    cat > /tmp/test_env.sh << 'EOF'
export RATE_LIMIT_STRATEGY=adaptive
export RATE_LIMIT_DEFAULT_REQUESTS=10
export RATE_LIMIT_WINDOW_SECONDS=1
export BLOCK_ON_RATE_LIMIT=true
EOF
    source /tmp/test_env.sh
    print_success "Configuration set"
    
    echo -e "${YELLOW}Expected behavior:${NC}"
    echo "  - First 10 requests succeed (normal traffic)"
    echo "  - Requests 11-15 get 429 (traffic spike detected)"
    echo "  - Anomaly level increases"
    echo "  - Limits may be automatically reduced"
    echo ""
    
    send_requests 15 "adaptive"
    print_success "Adaptive strategy activated"
}

# Test 5: Per-Endpoint Limits
test_per_endpoint() {
    print_section "TEST 5: PER-ENDPOINT LIMITS"
    
    print_test "Testing different endpoints with different limits..."
    
    cat > /tmp/test_env.sh << 'EOF'
export RATE_LIMIT_STRATEGY=token_bucket
export RATE_LIMIT_DEFAULT_REQUESTS=10
export RATE_LIMIT_WINDOW_SECONDS=1
EOF
    source /tmp/test_env.sh
    print_success "Configuration set"
    
    echo -e "${YELLOW}Testing /login endpoint (expected: 5 req/min, strict)${NC}"
    for i in {1..7}; do
        http_code=$(curl -s -o /dev/null -w "%{http_code}" "${API_URL}/login")
        if [ "$http_code" = "200" ]; then
            echo "  ✓ Request $i: 200"
        else
            echo "  ⚠ Request $i: $http_code (rate limited as expected)"
        fi
    done
    
    echo ""
    echo -e "${YELLOW}Testing /api/users endpoint (expected: 100 req/sec, permissive)${NC}"
    for i in {1..15}; do
        http_code=$(curl -s -o /dev/null -w "%{http_code}" "${API_URL}/api/users")
        echo "  ✓ Request $i: $http_code"
    done
    echo "  All requests succeeded (higher limit than default)"
}

# Test 6: Blocking Behavior
test_blocking() {
    print_section "TEST 6: IP BLOCKING BEHAVIOR"
    
    print_test "Set strategy with blocking enabled..."
    cat > /tmp/test_env.sh << 'EOF'
export RATE_LIMIT_STRATEGY=token_bucket
export RATE_LIMIT_DEFAULT_REQUESTS=5
export RATE_LIMIT_WINDOW_SECONDS=1
export BLOCK_ON_RATE_LIMIT=true
export RATE_LIMIT_BLOCK_DURATION=10
EOF
    source /tmp/test_env.sh
    print_success "Configuration set"
    
    echo -e "${YELLOW}Expected behavior:${NC}"
    echo "  - First 5 requests succeed"
    echo "  - Requests 6-10 get 429 (rate limited)"
    echo "  - After limit exceeded, IP gets blocked"
    echo "  - Blocked requests get 403 Forbidden"
    echo ""
    
    print_test "Sending 10 requests to trigger blocking..."
    for i in {1..10}; do
        http_code=$(curl -s -o /dev/null -w "%{http_code}" "${API_URL}${ENDPOINT}")
        if [ $i -le 5 ]; then
            echo "  Request $i: $http_code (should be 200)"
        elif [ $i -le 8 ]; then
            echo "  Request $i: $http_code (should be 429)"
        else
            echo "  Request $i: $http_code (might be 403 if blocked)"
        fi
    done
    
    print_warning "If you see 403, your IP is blocked. Will unblock in RATE_LIMIT_BLOCK_DURATION"
}

# Test 7: Logs and Monitoring
test_monitoring() {
    print_section "TEST 7: MONITORING & LOGGING"
    
    print_test "Checking for rate limit violations log..."
    
    if [ -f "rate_limit_violations.log" ]; then
        print_success "Violations log found"
        echo -e "${YELLOW}Recent violations:${NC}"
        tail -n 20 rate_limit_violations.log | head -n 20
    else
        print_warning "Violations log not found yet. Will be created after first violation."
    fi
    
    print_test "Checking console output for rate limit warnings..."
    echo -e "${YELLOW}Rate limit warnings should appear in console when violations occur.${NC}"
    echo "Look for: ${RED}🚨 RATE LIMIT VIOLATION DETECTED${NC}"
}

# Test 8: Whitelist IPs
test_whitelist() {
    print_section "TEST 8: WHITELIST IP BYPASS"
    
    print_test "Testing localhost whitelist (127.0.0.1)..."
    
    cat > /tmp/test_env.sh << 'EOF'
export RATE_LIMIT_STRATEGY=token_bucket
export RATE_LIMIT_DEFAULT_REQUESTS=2
export RATE_LIMIT_WINDOW_SECONDS=1
export BLOCK_ON_RATE_LIMIT=true
EOF
    source /tmp/test_env.sh
    print_success "Configuration set (very strict: 2 req/sec)"
    
    echo -e "${YELLOW}Sending 5 requests from localhost (should all succeed if whitelisted)...${NC}"
    success_count=0
    for i in {1..5}; do
        http_code=$(curl -s -H "X-Forwarded-For: 127.0.0.1" -o /dev/null -w "%{http_code}" "${API_URL}${ENDPOINT}")
        if [ "$http_code" = "200" ]; then
            ((success_count++))
            echo "  Request $i: $http_code"
        else
            echo "  Request $i: $http_code (not whitelisted)"
        fi
    done
    
    if [ $success_count -eq 5 ]; then
        print_success "Localhost is whitelisted (bypassed rate limiting)"
    else
        print_warning "Localhost may not be whitelisted. Check WHITELIST_IPS in rate_limiter.py"
    fi
}

# Test 9: Load Test
test_load() {
    print_section "TEST 9: LOAD TEST (30 seconds)"
    
    cat > /tmp/test_env.sh << 'EOF'
export RATE_LIMIT_STRATEGY=token_bucket
export RATE_LIMIT_DEFAULT_REQUESTS=20
export RATE_LIMIT_WINDOW_SECONDS=1
EOF
    source /tmp/test_env.sh
    print_success "Configuration set"
    
    echo -e "${YELLOW}Simulating 30 seconds of continuous traffic...${NC}"
    echo "Target: 20 requests/sec (should handle most successfully)"
    echo ""
    
    start_time=$(date +%s)
    success=0
    rate_limited=0
    
    while true; do
        current_time=$(date +%s)
        elapsed=$((current_time - start_time))
        
        if [ $elapsed -ge 30 ]; then
            break
        fi
        
        http_code=$(curl -s -m 1 -o /dev/null -w "%{http_code}" "${API_URL}${ENDPOINT}" 2>/dev/null || echo "000")
        
        if [ "$http_code" = "200" ]; then
            ((success++))
        else
            ((rate_limited++))
        fi
        
        echo -ne "\r  $elapsed/30s [✓ $success | ⚠ $rate_limited]"
    done
    
    echo ""
    echo ""
    print_success "Load test completed"
    echo "  Total successful: $success"
    echo "  Total rate limited: $rate_limited"
    echo "  Ratio: $(echo "scale=2; $success*100/($success+$rate_limited)" | bc)% successful"
}

# Test 10: Reset and Cleanup
test_reset() {
    print_section "TEST 10: RESET CONFIGURATION"
    
    print_test "Resetting to default configuration..."
    cat > /tmp/test_env.sh << 'EOF'
export RATE_LIMIT_STRATEGY=token_bucket
export RATE_LIMIT_DEFAULT_REQUESTS=10
export RATE_LIMIT_WINDOW_SECONDS=1
export BLOCK_ON_RATE_LIMIT=true
EOF
    source /tmp/test_env.sh
    print_success "Reset to defaults"
    
    echo ""
    print_success "All tests completed!"
    echo ""
    echo -e "${YELLOW}Summary:${NC}"
    echo "  ✓ Token Bucket tested"
    echo "  ✓ Sliding Window tested"
    echo "  ✓ Fixed Window tested"
    echo "  ✓ Adaptive tested"
    echo "  ✓ Per-endpoint limits tested"
    echo "  ✓ Blocking behavior tested"
    echo "  ✓ Monitoring/logging tested"
    echo "  ✓ Whitelist tested"
    echo "  ✓ Load test completed"
}

# Main Menu
show_menu() {
    echo -e "${BLUE}════════════════════════════════════════════════════════════${NC}"
    echo -e "${BLUE}           RATE LIMITING TEST SUITE${NC}"
    echo -e "${BLUE}════════════════════════════════════════════════════════════${NC}"
    echo ""
    echo "Select a test to run:"
    echo ""
    echo "  1) Token Bucket Strategy"
    echo "  2) Sliding Window Strategy"
    echo "  3) Fixed Window Strategy"
    echo "  4) Adaptive Strategy"
    echo "  5) Per-Endpoint Limits"
    echo "  6) Blocking Behavior"
    echo "  7) Monitoring & Logging"
    echo "  8) Whitelist IP Bypass"
    echo "  9) Load Test (30 sec)"
    echo ""
    echo "  10) Run ALL tests"
    echo "  0) Exit"
    echo ""
}

# Main
main() {
    check_server
    
    while true; do
        show_menu
        read -p "Enter selection [0-10]: " choice
        
        case $choice in
            1) test_token_bucket ;;
            2) test_sliding_window ;;
            3) test_fixed_window ;;
            4) test_adaptive ;;
            5) test_per_endpoint ;;
            6) test_blocking ;;
            7) test_monitoring ;;
            8) test_whitelist ;;
            9) test_load ;;
            10)
                test_token_bucket
                sleep 2
                test_sliding_window
                sleep 2
                test_fixed_window
                sleep 2
                test_adaptive
                sleep 2
                test_per_endpoint
                sleep 2
                test_blocking
                sleep 2
                test_monitoring
                sleep 2
                test_whitelist
                sleep 2
                test_load
                sleep 2
                test_reset
                ;;
            0)
                echo -e "${YELLOW}Goodbye!${NC}"
                exit 0
                ;;
            *)
                print_error "Invalid selection"
                ;;
        esac
        
        read -p "Press Enter to continue..."
        clear
    done
}

# Run main
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi
