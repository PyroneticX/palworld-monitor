#!/bin/bash

# PalWorld Server Update Script for EC2 (Linux)
# This script updates the PalWorld server on an AWS EC2 instance

set -e  # Exit on any error

# Source shared configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/config.sh"

print_status "Starting PalWorld server update on EC2 instance: $EC2_HOST"

# Validate configuration
if ! validate_config; then
    exit 1
fi

# Stop PalWorld server if running
print_step "Checking if PalWorld server is running..."
if check_service_status "palworld-server"; then
    print_status "Stopping PalWorld server..."
    remote_exec "sudo systemctl stop palworld-server"
    sleep 5
else
    print_warning "PalWorld server service not found or not running"
fi

# Check if steamcmd is installed
print_step "Checking SteamCMD installation..."
if ! remote_exec "test -d $STEAMCMD_DIR"; then
    print_status "Installing SteamCMD..."
    remote_exec "sudo mkdir -p $STEAMCMD_DIR && cd $STEAMCMD_DIR && wget -qO- 'https://steamcdn-a.akamaihd.net/client/installer/steamcmd_linux.tar.gz' | tar -xz"
    remote_exec "sudo chown -R $EC2_USER:$EC2_USER $STEAMCMD_DIR"
else
    print_status "SteamCMD already installed"
fi

# Update SteamCMD
print_step "Updating SteamCMD..."
remote_exec "cd $STEAMCMD_DIR && ./steamcmd.sh +quit"

# Create PalWorld server directory if it doesn't exist
print_step "Ensuring PalWorld server directory exists..."
remote_exec "sudo mkdir -p $PALWORLD_DIR && sudo chown -R $EC2_USER:$EC2_USER $PALWORLD_DIR"

# Update PalWorld server
print_step "Updating PalWorld server..."
remote_exec "cd $STEAMCMD_DIR && ./steamcmd.sh +login anonymous +force_install_dir $PALWORLD_DIR +app_update $PALWORLD_APP_ID validate +quit"

# Set proper permissions
print_status "Setting proper permissions..."
remote_exec "sudo chown -R $EC2_USER:$EC2_USER $PALWORLD_DIR"
remote_exec "chmod +x $PALWORLD_DIR/PalServer.sh"

# Create systemd service if it doesn't exist
print_step "Setting up systemd service..."
"$SCRIPT_DIR/create_systemd_service.sh"

# Start PalWorld server
print_step "Starting PalWorld server..."
remote_exec "sudo systemctl start palworld-server"

# Wait a moment and check status
sleep 10
print_step "Checking server status..."
if check_service_status "palworld-server"; then
    print_status "PalWorld server started successfully!"
    remote_exec "sudo systemctl status palworld-server --no-pager -l"
else
    print_error "Failed to start PalWorld server"
    remote_exec "sudo journalctl -u palworld-server --no-pager -l -n 20"
    exit 1
fi

print_status "PalWorld server update completed successfully!"
print_status "Server directory: $PALWORLD_DIR"
print_status "You can check server logs with: ssh $EC2_USER@$EC2_HOST 'sudo journalctl -u palworld-server -f'" 