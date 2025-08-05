#!/bin/bash

# PalWorld Dedicated Server Auto Start/Stop - EC2 Deployment Script (Linux)
# This script deploys the application to an AWS EC2 instance

set -e  # Exit on any error

# Source shared configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/config.sh"

print_status "Starting deployment to EC2 instance: $EC2_HOST"

# Validate configuration
if ! validate_config; then
    exit 1
fi

# Create remote directory if it doesn't exist
print_status "Creating remote directory: $REMOTE_DIR"
remote_exec "sudo mkdir -p $REMOTE_DIR && sudo chown $EC2_USER:$EC2_USER $REMOTE_DIR"

# Deploy application files using rsync for efficient transfers
print_status "Deploying application files using rsync..."

# Deploy src directory
print_status "Deploying src directory..."
rsync -avz --delete \
    -e "ssh -i $EC2_KEY_PATH -o StrictHostKeyChecking=no" \
    --exclude='*.json' \
    src/ "$EC2_USER@$EC2_HOST:$REMOTE_DIR/src/"

# Deploy individual files
print_status "Deploying configuration files..."
rsync -avz \
    -e "ssh -i $EC2_KEY_PATH -o StrictHostKeyChecking=no" \
    requirements.txt README.md LICENSE \
    "$EC2_USER@$EC2_HOST:$REMOTE_DIR/"

# Deploy images directory if it exists
if [ -d "images" ]; then
    print_status "Deploying images directory..."
    rsync -avz --delete \
        -e "ssh -i $EC2_KEY_PATH -o StrictHostKeyChecking=no" \
        --exclude='*.json' \
        images/ "$EC2_USER@$EC2_HOST:$REMOTE_DIR/images/"
fi

# Deploy data directory if it exists (excluding backups and recent_players.json)
if [ -d "data" ]; then
    print_status "Deploying data directory (excluding backups and recent_players.json)..."
    rsync -avz --delete \
        -e "ssh -i $EC2_KEY_PATH -o StrictHostKeyChecking=no" \
        --exclude='recent_players.json' \
        --exclude='*/backups/*' \
        --exclude='*.json' \
        data/ "$EC2_USER@$EC2_HOST:$REMOTE_DIR/data/"
fi

print_status "Deployment completed successfully!"

# Initialize virtual environment and install Python dependencies on the remote server
print_status "Setting up Python virtual environment and installing dependencies..."
remote_exec "cd $REMOTE_DIR && if [ ! -d 'venv' ]; then python3 -m venv venv; fi && venv/bin/pip install -r requirements.txt"
print_status "Dependencies installed successfully!"

print_status "Deployment to EC2 completed!"
print_status "Remote directory: $REMOTE_DIR"
print_status "You can now SSH into your EC2 instance and run the application from $REMOTE_DIR" 