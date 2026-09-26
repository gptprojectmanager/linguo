#!/usr/bin/env bash
# Linguo Automated Deployment & Health Check Script for Dell Precision 7670
set -euo pipefail

echo "🚀 Deploying Linguo to Dell Precision 7670..."

SYSTEMD_DIR="/etc/systemd/system"
CLOUDFLARE_DIR="/etc/cloudflared"
LINGUO_ROOT="/home/sam/linguo"

# 1. Check Python virtual environment
if [ ! -d "${LINGUO_ROOT}/.venv" ]; then
    echo "📦 Creating Python virtual environment in ${LINGUO_ROOT}/.venv..."
    python3 -m venv "${LINGUO_ROOT}/.venv"
    "${LINGUO_ROOT}/.venv/bin/pip" install --upgrade pip
    "${LINGUO_ROOT}/.venv/bin/pip" install -r "${LINGUO_ROOT}/requirements.txt"
fi

# 2. Install systemd service unit
if [ -d "${SYSTEMD_DIR}" ]; then
    echo "⚙️ Installing systemd service unit..."
    sudo cp "${LINGUO_ROOT}/config/linguo-server.service" "${SYSTEMD_DIR}/linguo-server.service"
    sudo systemctl daemon-reload
    sudo systemctl enable linguo-server.service
    sudo systemctl restart linguo-server.service
    echo "✅ systemd service linguo-server started"
fi

# 3. Check health endpoint locally
echo "🔍 Validating local service health on port 8765..."
sleep 2
HEALTH_CODE=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8765/health || echo "000")
if [ "${HEALTH_CODE}" = "200" ]; then
    echo "✅ Health check PASSED (HTTP 200)"
else
    echo "⚠️ Health check returned HTTP ${HEALTH_CODE} - inspect journalctl -u linguo-server -n 50"
fi

echo "🎉 Deployment check complete!"
