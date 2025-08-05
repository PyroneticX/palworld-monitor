#!/bin/bash

# PalWorld SystemD Service Creation Script
# This script creates and configures the systemd service for PalWorld server

set -e  # Exit on any error

# Source shared configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/config.sh"

print_status "Creating systemd service for PalWorld server..."

# Validate configuration
if ! validate_config; then
    exit 1
fi

# Check if systemd service already exists
print_step "Checking if systemd service already exists..."
if remote_exec "test -f /etc/systemd/system/palworld-control.service"; then
    print_status "Systemd service already exists"
    print_status "Current service configuration:"
    remote_exec "sudo cat /etc/systemd/system/palworld-control.service"
    exit 0
fi

# Create the systemd service file
print_step "Creating systemd service configuration..."
remote_exec "sudo tee /etc/systemd/system/palworld-control.service > /dev/null << 'EOF'
[Unit]
Description=PalWorld Control Application
After=network.target

[Service]
Type=simple
User=ubuntu
WorkingDirectory=$REMOTE_DIR
ExecStart=$REMOTE_DIR/venv/bin/python.exe $REMOTE_DIR/src/main.py
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal
Environment=PYTHONPATH=$REMOTE_DIR/src

[Install]
WantedBy=multi-user.target
EOF"

# Reload systemd daemon
print_step "Reloading systemd daemon..."
remote_exec "sudo systemctl daemon-reload"

# Enable the service
print_step "Enabling PalWorld control service..."
remote_exec "sudo systemctl enable palworld-control"

print_status "Systemd service created and enabled successfully!"
print_status "Service file location: /etc/systemd/system/palworld-control.service"

# Show the created service configuration
print_status "Service configuration:"
remote_exec "sudo cat /etc/systemd/system/palworld-control.service"

print_status "You can now manage the service with:"
print_status "  sudo systemctl start palworld-control"
print_status "  sudo systemctl stop palworld-control"
print_status "  sudo systemctl restart palworld-control"
print_status "  sudo systemctl status palworld-control" 