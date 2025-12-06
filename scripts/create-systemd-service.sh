#!/bin/bash
# Script to create systemd service for auto-starting Docker Compose services on boot

set -e

PROJECT_DIR="/home/jdehart/Working/lmsvr"
SERVICE_NAME="lmsvr-docker-compose"
SERVICE_FILE="/etc/systemd/system/${SERVICE_NAME}.service"
USER=$(whoami)

echo "Creating systemd service for Docker Compose auto-start..."

# Create the systemd service file
sudo tee "$SERVICE_FILE" <<EOF
[Unit]
Description=LMSVR Docker Compose Services
Requires=docker.service
After=docker.service network-online.target
Wants=network-online.target

[Service]
Type=oneshot
RemainAfterExit=yes
WorkingDirectory=${PROJECT_DIR}
User=${USER}
Group=${USER}
ExecStart=/usr/bin/docker compose up -d
ExecStop=/usr/bin/docker compose down
TimeoutStartSec=0

[Install]
WantedBy=multi-user.target
EOF

echo "Service file created at: $SERVICE_FILE"
echo ""
echo "To enable the service, run:"
echo "  sudo systemctl daemon-reload"
echo "  sudo systemctl enable ${SERVICE_NAME}"
echo ""
echo "To start the service now:"
echo "  sudo systemctl start ${SERVICE_NAME}"
echo ""
echo "To check status:"
echo "  sudo systemctl status ${SERVICE_NAME}"











