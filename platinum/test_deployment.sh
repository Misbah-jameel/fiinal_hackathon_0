#!/bin/bash
# Platinum Tier - Deployment & Configuration Test Script
# Run this to verify everything is working

set -e

echo "========================================="
echo "AI Employee - Platinum Tier"
echo "Deployment & Configuration Test"
echo "========================================="
echo ""

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

pass() {
    echo -e "${GREEN}✓${NC} $1"
}

fail() {
    echo -e "${RED}✗${NC} $1"
}

warn() {
    echo -e "${YELLOW}!${NC} $1"
}

# Test counter
total=0
passed=0
failed=0

# Section header
section() {
    echo ""
    echo "-----------------------------------------"
    echo "$1"
    echo "-----------------------------------------"
}

# ===========================================
# Test 1: Python Environment
# ===========================================
section "1. Python Environment"

total=$((total+1))
if python --version > /dev/null 2>&1; then
    pass "Python installed: $(python --version 2>&1)"
    passed=$((passed+1))
else
    fail "Python not found"
    failed=$((failed+1))
fi

total=$((total+1))
if pip show python-dotenv > /dev/null 2>&1; then
    pass "python-dotenv installed"
    passed=$((passed+1))
else
    warn "python-dotenv not installed, run: pip install python-dotenv"
    failed=$((failed+1))
fi

# ===========================================
# Test 2: Git Repository
# ===========================================
section "2. Git Repository"

total=$((total+1))
if [ -d "AI_Employee_Vault/.git" ]; then
    pass "Git repository initialized"
    passed=$((passed+1))
else
    fail "Git repository not found"
    failed=$((failed+1))
fi

total=$((total+1))
if [ -f "AI_Employee_Vault/.gitignore" ]; then
    pass ".gitignore exists"
    passed=$((passed+1))
else
    fail ".gitignore not found"
    failed=$((failed+1))
fi

# ===========================================
# Test 3: Module Imports
# ===========================================
section "3. Platinum Module Imports"

total=$((total+1))
if python -c "from platinum.cloud_agent import config" 2>/dev/null; then
    pass "Cloud Agent config module OK"
    passed=$((passed+1))
else
    fail "Cloud Agent config module failed"
    failed=$((failed+1))
fi

total=$((total+1))
if python -c "from platinum.local_agent import config" 2>/dev/null; then
    pass "Local Agent config module OK"
    passed=$((passed+1))
else
    fail "Local Agent config module failed"
    failed=$((failed+1))
fi

total=$((total+1))
if python -c "from platinum.sync import vault_sync" 2>/dev/null; then
    pass "Vault Sync module OK"
    passed=$((passed+1))
else
    fail "Vault Sync module failed"
    failed=$((failed+1))
fi

# ===========================================
# Test 4: Environment Configuration
# ===========================================
section "4. Environment Configuration"

total=$((total+1))
if [ -f ".env" ]; then
    pass ".env file exists"
    passed=$((passed+1))
else
    fail ".env file not found"
    failed=$((failed+1))
fi

total=$((total+1))
if grep -q "DRY_RUN=true" .env 2>/dev/null; then
    pass "DRY_RUN mode enabled (safe)"
    passed=$((passed+1))
else
    warn "DRY_RUN not set or false"
    failed=$((failed+1))
fi

total=$((total+1))
if grep -q "GIT_REMOTE_URL=" .env 2>/dev/null; then
    pass "GIT_REMOTE_URL configured"
    passed=$((passed+1))
else
    warn "GIT_REMOTE_URL not configured"
    failed=$((failed+1))
fi

# ===========================================
# Test 5: Docker Environment
# ===========================================
section "5. Docker Environment"

total=$((total+1))
if command -v docker > /dev/null 2>&1; then
    pass "Docker installed: $(docker --version 2>&1)"
    passed=$((passed+1))
else
    warn "Docker not installed (required for Cloud VM)"
    failed=$((failed+1))
fi

total=$((total+1))
if command -v docker-compose > /dev/null 2>&1; then
    pass "Docker Compose installed: $(docker-compose --version 2>&1)"
    passed=$((passed+1))
else
    warn "Docker Compose not installed (required for Cloud VM)"
    failed=$((failed+1))
fi

# ===========================================
# Test 6: Vault Structure
# ===========================================
section "6. Vault Structure"

vault_dirs=(
    "AI_Employee_Vault/Needs_Action"
    "AI_Employee_Vault/Plans"
    "AI_Employee_Vault/Pending_Approval"
    "AI_Employee_Vault/Approved"
    "AI_Employee_Vault/Done"
    "AI_Employee_Vault/Logs"
    "AI_Employee_Vault/Audit"
)

for dir in "${vault_dirs[@]}"; do
    total=$((total+1))
    if [ -d "$dir" ]; then
        pass "Directory exists: $dir"
        passed=$((passed+1))
    else
        fail "Directory missing: $dir"
        failed=$((failed+1))
    fi
done

# ===========================================
# Test 7: Demo Flow
# ===========================================
section "7. Demo Flow Test"

total=$((total+1))
if [ -f "platinum/demo_flow.py" ]; then
    pass "Demo flow script exists"
    passed=$((passed+1))
else
    fail "Demo flow script not found"
    failed=$((failed+1))
fi

# ===========================================
# Test 8: Documentation
# ===========================================
section "8. Documentation"

docs=(
    "platinum/README.md"
    "platinum/QUICKSTART.md"
    "platinum/DEPLOYMENT_GUIDE.md"
    "platinum/CREDENTIALS_SETUP.md"
    "platinum/IMPLEMENTATION_SUMMARY.md"
)

for doc in "${docs[@]}"; do
    total=$((total+1))
    if [ -f "$doc" ]; then
        pass "Documentation exists: $doc"
        passed=$((passed+1))
    else
        fail "Documentation missing: $doc"
        failed=$((failed+1))
    fi
done

# ===========================================
# Summary
# ===========================================
echo ""
echo "========================================="
echo "Test Summary"
echo "========================================="
echo "Total Tests:  $total"
echo -e "Passed:       ${GREEN}$passed${NC}"
echo -e "Failed:       ${RED}$failed${NC}"
echo "Success Rate: $((passed*100/total))%"
echo ""

if [ $failed -eq 0 ]; then
    echo -e "${GREEN}✓ All tests passed! Platinum Tier ready for deployment.${NC}"
    exit 0
else
    echo -e "${YELLOW}! Some tests failed. Please review and fix the issues above.${NC}"
    echo ""
    echo "Next Steps:"
    echo "1. Fix failed tests"
    echo "2. Configure .env file"
    echo "3. Set up Git remote for vault sync"
    echo "4. Deploy to Cloud VM (optional)"
    exit 1
fi
