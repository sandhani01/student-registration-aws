#!/usr/bin/env bash
# ==============================================================================
# Amazon EC2 User Data Bootstrap Script
# Operating System: Amazon Linux 2023
# Purpose: Automated Provisioning for Student Registration Web App
# ==============================================================================

set -euo pipefail

echo "=========================================================="
echo "Starting Student Registration System Provisioning..."
echo "Date: $(date -u)"
echo "=========================================================="

# ------------------------------------------------------------------------------
# 1. Configuration Placeholders (Replace with your actual assignment values)
# ------------------------------------------------------------------------------
STUDENT_ROLL_NO="<MY_UNIVERSITY_ROLL_NUMBER>"
AWS_REGION="us-east-1"
DYNAMODB_TABLE="Students-${STUDENT_ROLL_NO}"
SNS_TOPIC_ARN="arn:aws:sns:${AWS_REGION}:<AWS_ACCOUNT_ID>:StudentRegistration-${STUDENT_ROLL_NO}"
APP_DIR="/opt/student-registration"
LOG_DIR="/var/log/student-registration"

# ------------------------------------------------------------------------------
# 2. System Package Updates & Dependencies Installation
# ------------------------------------------------------------------------------
echo "Updating packages and installing system dependencies..."
dnf update -y
dnf install -y python3 python3-pip git nginx

# ------------------------------------------------------------------------------
# 3. Create Application & Log Directories
# ------------------------------------------------------------------------------
echo "Configuring directories at ${APP_DIR}..."
mkdir -p "${APP_DIR}"
mkdir -p "${LOG_DIR}"
chown -R ec2-user:ec2-user "${APP_DIR}"
chown -R ec2-user:ec2-user "${LOG_DIR}"

# ------------------------------------------------------------------------------
# 4. Set Up Application Environment File
# ------------------------------------------------------------------------------
echo "Generating /etc/student-registration.env..."
cat <<EOF > /etc/student-registration.env
# Student Application Environment Variables
ROLL_NO=${STUDENT_ROLL_NO}
AWS_REGION=${AWS_REGION}
DYNAMODB_TABLE=${DYNAMODB_TABLE}
SNS_TOPIC_ARN=${SNS_TOPIC_ARN}
FLASK_ENV=production
FLASK_DEBUG=False
SECRET_KEY=$(python3 -c "import secrets; print(secrets.token_hex(24))")
PORT=5000
HOST=127.0.0.1
EOF

chmod 600 /etc/student-registration.env
chown ec2-user:ec2-user /etc/student-registration.env

# ------------------------------------------------------------------------------
# 5. Application Code Setup
# ------------------------------------------------------------------------------
# If deploying from a Git repository, replace this URL with your repo:
# GIT_REPO="https://github.com/your-username/student-registration-aws.git"
# sudo -u ec2-user git clone "${GIT_REPO}" "${APP_DIR}"

# Set up Python virtual environment
echo "Setting up Python virtual environment in ${APP_DIR}/venv..."
sudo -u ec2-user python3 -m venv "${APP_DIR}/venv"
sudo -u ec2-user "${APP_DIR}/venv/bin/pip" install --upgrade pip

# Install required python packages
if [ -f "${APP_DIR}/requirements.txt" ]; then
    echo "Installing requirements from ${APP_DIR}/requirements.txt..."
    sudo -u ec2-user "${APP_DIR}/venv/bin/pip" install -r "${APP_DIR}/requirements.txt"
else
    echo "Installing base requirements..."
    sudo -u ec2-user "${APP_DIR}/venv/bin/pip" install Flask boto3 gunicorn python-dotenv
fi

# ------------------------------------------------------------------------------
# 6. Configure Systemd Service
# ------------------------------------------------------------------------------
echo "Configuring systemd service..."
cat <<EOF > /etc/systemd/system/student-registration.service
[Unit]
Description=Student Registration System (Gunicorn WSGI Application)
After=network.target

[Service]
Type=simple
User=ec2-user
Group=ec2-user
WorkingDirectory=${APP_DIR}
EnvironmentFile=/etc/student-registration.env
ExecStart=${APP_DIR}/venv/bin/gunicorn --workers 3 --bind 127.0.0.1:5000 --timeout 60 --access-logfile ${LOG_DIR}/access.log --error-logfile ${LOG_DIR}/error.log app:app
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
systemctl enable student-registration.service

# ------------------------------------------------------------------------------
# 7. Configure Nginx Reverse Proxy on Port 80
# ------------------------------------------------------------------------------
echo "Configuring Nginx reverse proxy on port 80..."
cat <<EOF > /etc/nginx/conf.d/student-registration.conf
server {
    listen 80;
    listen [::]:80;
    server_name _;

    client_max_body_size 10M;

    location /static/ {
        alias ${APP_DIR}/static/;
        expires 7d;
    }

    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_http_version 1.1;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }
}
EOF

# Ensure default nginx welcome page does not clash
sed -i 's/listen       80 default_server;/listen       8080 default_server;/g' /etc/nginx/nginx.conf 2>/dev/null || true

systemctl enable nginx
systemctl restart nginx

# Start student application
systemctl restart student-registration.service

# ------------------------------------------------------------------------------
# 8. Post-Provisioning Health Verification
# ------------------------------------------------------------------------------
sleep 3
echo "Checking service status..."
if curl -s http://127.0.0.1/health | grep -q "healthy"; then
    echo "SUCCESS: Student Registration Web Application is healthy and serving requests on port 80!"
else
    echo "WARNING: Health check did not return healthy. Check logs at journalctl -u student-registration"
fi

echo "=========================================================="
echo "Provisioning Complete! Access via EC2 Public IPv4 Address."
echo "=========================================================="
