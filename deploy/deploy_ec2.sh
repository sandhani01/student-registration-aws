#!/usr/bin/env bash
# ==============================================================================
# Script: deploy_ec2.sh
# Purpose: Idempotent Deployment & Verification for Amazon Linux 2023
# Target: EC2 Instance i-09a305ec90d53a8ba (Students-24BCA7871)
# ==============================================================================

set -euo pipefail

echo "=========================================================="
echo "Starting Student Registration Deployment Pipeline..."
echo "Date: $(date -u '+%Y-%m-%d %H:%M:%S UTC')"
echo "=========================================================="

# 1. Configuration Constants
ROLL_NO="24BCA7871"
AWS_REGION="us-east-1"
DYNAMODB_TABLE="Students-24BCA7871"
SNS_TOPIC_ARN="arn:aws:sns:us-east-1:394943564062:StudentRegistration-24BCA7871"

APP_DIR="/opt/student-registration"
VENV_DIR="${APP_DIR}/venv"
PYTHON_BIN="${VENV_DIR}/bin/python3"
LOG_DIR="/var/log/student-registration"
SYS_ENV="/etc/student-registration.env"
APP_ENV="${APP_DIR}/.env"

echo "[1/6] Verifying application directory and Python virtualenv..."
if [ ! -d "${APP_DIR}" ]; then
    echo "ERROR: Directory ${APP_DIR} does not exist!" >&2
    exit 1
fi

if [ ! -f "${APP_DIR}/app.py" ]; then
    echo "ERROR: ${APP_DIR}/app.py was not found!" >&2
    exit 1
fi

if [ ! -x "${PYTHON_BIN}" ]; then
    echo "Creating virtual environment at ${VENV_DIR}..."
    python3 -m venv "${VENV_DIR}"
    "${VENV_DIR}/bin/pip" install --upgrade pip
    if [ -f "${APP_DIR}/requirements.txt" ]; then
        "${VENV_DIR}/bin/pip" install -r "${APP_DIR}/requirements.txt"
    else
        "${VENV_DIR}/bin/pip" install Flask boto3 gunicorn python-dotenv
    fi
fi

# Ensure gunicorn binary is present in virtualenv
if ! "${VENV_DIR}/bin/gunicorn" --version &>/dev/null; then
    echo "Installing Gunicorn in virtual environment..."
    "${VENV_DIR}/bin/pip" install gunicorn
fi

# 2. Environment Variables & Secure SECRET_KEY
echo "[2/6] Configuring environment files..."
SECRET_KEY=""
if [ -f "${SYS_ENV}" ]; then
    SECRET_KEY=$(grep -E "^SECRET_KEY=" "${SYS_ENV}" 2>/dev/null | cut -d'=' -f2- | tr -d ' "\r' || true)
fi
if [ -z "${SECRET_KEY}" ] && [ -f "${APP_ENV}" ]; then
    SECRET_KEY=$(grep -E "^SECRET_KEY=" "${APP_ENV}" 2>/dev/null | cut -d'=' -f2- | tr -d ' "\r' || true)
fi

if [ -z "${SECRET_KEY}" ] || [ "${SECRET_KEY}" = "replace-with-a-secure-random-secret-key-32-chars-long" ] || [ "${SECRET_KEY}" = "dev-secret-key-change-in-prod-12345" ]; then
    SECRET_KEY=$("${PYTHON_BIN}" -c "import secrets; print(secrets.token_hex(32))")
    echo "Generated new cryptographically secure 256-bit SECRET_KEY."
else
    echo "Preserved existing secure SECRET_KEY."
fi

# Write system environment file
cat <<EOF > "${SYS_ENV}"
ROLL_NO=${ROLL_NO}
AWS_REGION=${AWS_REGION}
DYNAMODB_TABLE=${DYNAMODB_TABLE}
SNS_TOPIC_ARN=${SNS_TOPIC_ARN}
FLASK_ENV=production
FLASK_DEBUG=False
SECRET_KEY=${SECRET_KEY}
PORT=5000
HOST=127.0.0.1
EOF
chmod 600 "${SYS_ENV}"
chown ec2-user:ec2-user "${SYS_ENV}"

# Write application environment file
cat <<EOF > "${APP_ENV}"
ROLL_NO=${ROLL_NO}
AWS_REGION=${AWS_REGION}
DYNAMODB_TABLE=${DYNAMODB_TABLE}
SNS_TOPIC_ARN=${SNS_TOPIC_ARN}
FLASK_ENV=production
FLASK_DEBUG=False
SECRET_KEY=${SECRET_KEY}
PORT=5000
HOST=127.0.0.1
EOF
chmod 600 "${APP_ENV}"
chown ec2-user:ec2-user "${APP_ENV}"

# Ensure permissions across application directory
mkdir -p "${LOG_DIR}"
chown -R ec2-user:ec2-user "${LOG_DIR}"
chmod 755 "${LOG_DIR}"
chown -R ec2-user:ec2-user "${APP_DIR}"

# 3. Read-Only AWS IAM Validation (No fake registrations, no test emails)
echo "[3/6] Validating IAM permissions for DynamoDB & SNS..."
"${PYTHON_BIN}" -c '
import sys, boto3
region = "us-east-1"
table_name = "Students-24BCA7871"
topic_arn = "arn:aws:sns:us-east-1:394943564062:StudentRegistration-24BCA7871"

# Check STS
try:
    sts = boto3.client("sts", region_name=region)
    caller = sts.get_caller_identity()
    print("  [PASS] IAM Role attached:", caller.get("Arn"))
except Exception as e:
    print("  [WARN] STS verification:", e)

# Check DynamoDB (describe only)
try:
    dynamodb = boto3.client("dynamodb", region_name=region)
    res = dynamodb.describe_table(TableName=table_name)
    print("  [PASS] DynamoDB Table active:", res.get("Table", {}).get("TableStatus"))
except Exception as e:
    print("  [FAIL] DynamoDB check error:", e)
    sys.exit(1)

# Check SNS (get attributes only)
try:
    sns = boto3.client("sns", region_name=region)
    res = sns.get_topic_attributes(TopicArn=topic_arn)
    print("  [PASS] Amazon SNS Topic accessible:", topic_arn)
except Exception as e:
    print("  [FAIL] SNS check error:", e)
    sys.exit(1)
'

# 4. Systemd Service Configuration
echo "[4/6] Setting up systemd service student-registration..."
cat <<EOF > /etc/systemd/system/student-registration.service
[Unit]
Description=Student Registration System (Gunicorn WSGI Application)
Documentation=https://github.com/aws/
After=network.target

[Service]
Type=simple
User=ec2-user
Group=ec2-user
WorkingDirectory=${APP_DIR}
EnvironmentFile=-${SYS_ENV}
EnvironmentFile=-${APP_ENV}
ExecStart=${VENV_DIR}/bin/gunicorn --workers 3 --bind 127.0.0.1:5000 --timeout 60 --access-logfile ${LOG_DIR}/access.log --error-logfile ${LOG_DIR}/error.log --capture-output app:app
Restart=always
RestartSec=5
KillSignal=SIGTERM
TimeoutStopSec=10

PrivateTmp=true

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
systemctl enable student-registration.service
systemctl restart student-registration.service

sleep 2
if systemctl is-active --quiet student-registration.service; then
    echo "  [PASS] Service student-registration is ACTIVE."
else
    echo "  [FAIL] Service student-registration failed to start! Recent logs:"
    journalctl -u student-registration.service -n 25 --no-pager
    exit 1
fi

# 5. Nginx Configuration
echo "[5/6] Configuring Nginx reverse proxy..."
if ! command -v nginx &>/dev/null; then
    echo "Installing Nginx via dnf..."
    dnf install -y nginx
fi

# Prevent default server block collision on port 80 in Amazon Linux 2023
if [ -f /etc/nginx/nginx.conf ]; then
    sed -i 's/listen       80 default_server;/listen       8080 default_server;/g' /etc/nginx/nginx.conf 2>/dev/null || true
    sed -i 's/listen       \[::\]:80 default_server;/listen       \[::\]:8080 default_server;/g' /etc/nginx/nginx.conf 2>/dev/null || true
fi

cat <<EOF > /etc/nginx/conf.d/student-registration.conf
server {
    listen 80 default_server;
    listen [::]:80 default_server;
    server_name _;

    client_max_body_size 10M;

    location /static/ {
        alias ${APP_DIR}/static/;
        expires 7d;
        add_header Cache-Control "public, max-age=604800, immutable";
    }

    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_http_version 1.1;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_connect_timeout 60s;
        proxy_read_timeout 60s;
        proxy_send_timeout 60s;
    }

    location /health {
        proxy_pass http://127.0.0.1:5000/health;
        proxy_set_header Host \$host;
        access_log off;
    }
}
EOF

nginx -t
systemctl enable nginx
systemctl restart nginx

if systemctl is-active --quiet nginx; then
    echo "  [PASS] Nginx is ACTIVE and listening on port 80."
else
    echo "  [FAIL] Nginx failed to start! Recent logs:"
    journalctl -u nginx -n 25 --no-pager
    exit 1
fi

# 6. Verification
echo "[6/6] Verifying application endpoints..."
sleep 2

# Check direct Gunicorn port 5000
GUNICORN_CODE=$(curl -s -o /dev/null -w "%{http_code}" http://127.0.0.1:5000/health || echo "000")
if [ "${GUNICORN_CODE}" -eq 200 ]; then
    echo "  [PASS] Direct Gunicorn (http://127.0.0.1:5000/health): HTTP 200 OK"
else
    echo "  [FAIL] Direct Gunicorn returned HTTP ${GUNICORN_CODE}"
    journalctl -u student-registration.service -n 25 --no-pager
    exit 1
fi

# Check Nginx port 80
HEALTH_JSON=$(curl -s http://127.0.0.1/health || true)
if echo "${HEALTH_JSON}" | grep -q '"status":\s*"healthy"'; then
    echo "  [PASS] Nginx reverse proxy (http://127.0.0.1/health): Responsive!"
    echo "  Health response: ${HEALTH_JSON}"
else
    echo "  [FAIL] Health check failed! Response: ${HEALTH_JSON}"
    exit 1
fi

echo "=========================================================="
echo "DEPLOYMENT COMPLETE!"
echo "Public Website URL: http://54.227.84.188/"
echo "Health Endpoint:    http://54.227.84.188/health"
echo "=========================================================="
