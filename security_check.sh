#!/bin/bash

# Sovereign AI Gateway - Pre-Deployment Security Checklist
# Run this script before deploying to production

set -e

echo "🛡️  Sovereign AI Gateway - Security Verification"
echo "================================================"
echo ""

# Color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

PASSED=0
FAILED=0
WARNINGS=0

# Function to check
check() {
    local name=$1
    local command=$2
    local expected=$3
    
    echo -n "Checking $name... "
    
    if eval "$command" > /dev/null 2>&1; then
        echo -e "${GREEN}✅ PASS${NC}"
        ((PASSED++))
    else
        echo -e "${RED}❌ FAIL${NC}"
        echo "   Expected: $expected"
        ((FAILED++))
    fi
}

# Function for warnings
warn() {
    local name=$1
    local message=$2
    
    echo -e "${YELLOW}⚠️  WARNING: $name${NC}"
    echo "   $message"
    ((WARNINGS++))
}

# 1. CRITICAL: LiteLLM Version
echo "1. Dependency Security"
echo "----------------------"
LITELLM_VERSION=$(pip list 2>/dev/null | grep litellm | awk '{print $2}' || echo "0.0.0")
if [ "$(printf '%s\n' "1.81.0" "$LITELLM_VERSION" | sort -V | head -n1)" = "1.81.0" ]; then
    echo -e "${GREEN}✅ PASS${NC} LiteLLM version: $LITELLM_VERSION (>= 1.81.0)"
    ((PASSED++))
else
    echo -e "${RED}❌ FAIL${NC} LiteLLM version: $LITELLM_VERSION (< 1.81.0)"
    echo "   🚨 CRITICAL: Vulnerable to CVE-2024-5751, CVE-2024-6825"
    echo "   Run: pip install litellm>=1.81.0"
    ((FAILED++))
fi
echo ""

# 2. Ollama Binding
echo "2. Ollama Security"
echo "------------------"
if command -v netstat > /dev/null 2>&1; then
    if netstat -an 2>/dev/null | grep -q "127.0.0.1:11434"; then
        echo -e "${GREEN}✅ PASS${NC} Ollama bound to localhost only"
        ((PASSED++))
    elif netstat -an 2>/dev/null | grep -q "0.0.0.0:11434"; then
        echo -e "${RED}❌ FAIL${NC} Ollama exposed on all interfaces (0.0.0.0)"
        echo "   Run: export OLLAMA_HOST=127.0.0.1:11434 && ollama serve"
        ((FAILED++))
    else
        warn "Ollama binding" "Cannot verify Ollama binding (not running?)"
    fi
else
    warn "Network tools" "netstat not available, cannot verify Ollama binding"
fi
echo ""

# 3. API Key Security
echo "3. Authentication"
echo "-----------------"
if [ -f ".env" ]; then
    GATEWAY_KEY=$(grep GATEWAY_API_KEY .env | cut -d'=' -f2 | tr -d ' "'"'"'')
    if [ "$GATEWAY_KEY" = "default-dev-key" ]; then
        echo -e "${RED}❌ FAIL${NC} Using default API key"
        echo "   Generate secure key: openssl rand -hex 32"
        ((FAILED++))
    elif [ ${#GATEWAY_KEY} -lt 32 ]; then
        echo -e "${RED}❌ FAIL${NC} API key too short (${#GATEWAY_KEY} chars)"
        echo "   Generate 256-bit key: openssl rand -hex 32"
        ((FAILED++))
    else
        echo -e "${GREEN}✅ PASS${NC} Strong API key configured (${#GATEWAY_KEY} chars)"
        ((PASSED++))
    fi
else
    echo -e "${RED}❌ FAIL${NC} .env file not found"
    echo "   Copy .env.example to .env and configure"
    ((FAILED++))
fi
echo ""

# 4. OpenAI Key Present
echo "4. LLM Configuration"
echo "--------------------"
if [ -f ".env" ]; then
    if grep -q "OPENAI_API_KEY=sk-" .env; then
        echo -e "${GREEN}✅ PASS${NC} OpenAI API key configured"
        ((PASSED++))
    else
        echo -e "${RED}❌ FAIL${NC} OpenAI API key missing or invalid"
        ((FAILED++))
    fi
else
    echo -e "${RED}❌ FAIL${NC} Cannot check OpenAI key (.env missing)"
    ((FAILED++))
fi
echo ""

# 5. Required Files
echo "5. Required Files"
echo "-----------------"
check "api_server.py" "[ -f api_server.py ]" "File

