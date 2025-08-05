#!/bin/bash

# PalWorld Dedicated Server - Config Data Management Script (Linux)
# This script manages PalWorld server configuration files between local and remote server

set -e  # Exit on any error

# Source shared configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/config.sh"

# Config data configuration
CONFIG_DIR="$PALWORLD_DIR/Pal/Saved/Config/WindowsServer"
CONFIG_FILE="PalWorldSettings.ini"
REMOTE_CONFIG_PATH="$CONFIG_DIR/$CONFIG_FILE"

# Function to show usage
show_usage() {
    echo "Usage: $0 {pull|push} [file_path] [options]"
    echo ""
    echo "Commands:"
    echo "  pull     - Download PalWorld config from EC2 server to current directory"
    echo "  push     - Upload local PalWorld config file to EC2 server"
    echo ""
    echo "Arguments:"
    echo "  file_path - Path to config file (required for push command)"
    echo ""
    echo "Options:"
    echo "  --backup - Create backup before operation (for push command)"
    echo "  --force  - Skip confirmation prompts"
    echo ""
    echo "Examples:"
    echo "  $0 pull                    # Download config to current directory"
    echo "  $0 push /path/to/config.ini # Upload config file to server"
    echo "  $0 push config.ini --backup # Create backup before pushing"
    echo "  $0 push config.ini --force  # Skip confirmation prompts"
}

# Function to create backup
create_backup() {
    local backup_name="config_backup_$(date +%Y%m%d_%H%M%S)"
    local backup_path="$BACKUP_DIR/$backup_name"
    
    print_status "Creating backup: $backup_path"
    mkdir -p "$BACKUP_DIR"
    
    if [ -f "$LOCAL_CONFIG_FILE" ]; then
        cp "$LOCAL_CONFIG_FILE" "$backup_path"
        print_status "Backup created: $backup_path"
    else
        print_warning "No local config file to backup"
    fi
}

# Function to pull config data from server
pull_config() {
    # Set local config file path to current directory
    LOCAL_CONFIG_FILE="./$CONFIG_FILE"
    BACKUP_DIR="./backups"
    
    print_status "Pulling PalWorld config from EC2 server..."
    
    # Validate configuration
    if ! validate_config; then
        exit 1
    fi
    
    # Check if config directory exists on server
    print_step "Checking config directory on server..."
    if ! remote_exec "test -d $CONFIG_DIR"; then
        print_error "Config directory not found on server: $CONFIG_DIR"
        print_error "Make sure PalWorld server is properly installed"
        exit 1
    fi
    
    # Check if config file exists on server
    print_step "Checking config file on server..."
    if ! remote_exec "test -f $REMOTE_CONFIG_PATH"; then
        print_error "Config file not found on server: $REMOTE_CONFIG_PATH"
        print_error "Make sure PalWorld server is properly configured"
        exit 1
    fi
    
    # Download config file
    print_step "Downloading config file..."
    scp -i "$EC2_KEY_PATH" -o StrictHostKeyChecking=no "$EC2_USER@$EC2_HOST:$REMOTE_CONFIG_PATH" "$LOCAL_CONFIG_FILE"
    
    print_status "Config file downloaded successfully!"
    print_status "Local config file: $LOCAL_CONFIG_FILE"
}

# Function to push config data to server
push_config() {
    local config_file="$1"
    local force=false
    local create_backup_flag=false
    
    # Check if config file path is provided
    if [ -z "$config_file" ]; then
        print_error "Config file path is required for push command"
        show_usage
        exit 1
    fi
    
    # Set local config file path
    LOCAL_CONFIG_FILE="$config_file"
    BACKUP_DIR="$(dirname "$config_file")/backups"
    
    # Parse options
    while [[ $# -gt 0 ]]; do
        case $1 in
            --force)
                force=true
                shift
                ;;
            --backup)
                create_backup_flag=true
                shift
                ;;
            *)
                echo "Unknown option: $1"
                show_usage
                exit 1
                ;;
        esac
    done
    
    print_status "Pushing PalWorld config to EC2 server..."
    
    # Validate configuration
    if ! validate_config; then
        exit 1
    fi
    
    # Check if local config file exists
    if [ ! -f "$LOCAL_CONFIG_FILE" ]; then
        print_error "Local config file not found: $LOCAL_CONFIG_FILE"
        print_error "Please provide a valid path to the config file"
        exit 1
    fi
    
    # Create backup if requested
    if [ "$create_backup_flag" = true ]; then
        create_backup
    fi
    
    # Confirm operation unless --force is used
    if [ "$force" = false ]; then
        echo ""
        print_warning "This will replace the PalWorld config file on the server!"
        print_warning "Make sure the PalWorld server is stopped before pushing config."
        echo ""
        read -p "Are you sure you want to continue? (y/n): " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            print_status "Operation cancelled"
            exit 0
        fi
    fi
    
    # Check if server is running and warn user
    print_step "Checking server status..."
    if check_service_status "palworld-server"; then
        print_warning "PalWorld server appears to be running!"
        print_warning "It's recommended to stop the server before pushing config."
        if [ "$force" = false ]; then
            read -p "Continue anyway? (y/n): " -n 1 -r
            echo
            if [[ ! $REPLY =~ ^[Yy]$ ]]; then
                print_status "Operation cancelled"
                exit 0
            fi
        fi
    fi
    
    # Create backup directory on server
    print_step "Creating backup on server..."
    remote_exec "sudo mkdir -p $CONFIG_DIR/backups"
    remote_exec "sudo chown $EC2_USER:$EC2_USER $CONFIG_DIR/backups"
    
    # Create server backup
    local server_backup_name="server_config_backup_$(date +%Y%m%d_%H%M%S)"
    remote_exec "if [ -f '$REMOTE_CONFIG_PATH' ]; then cp '$REMOTE_CONFIG_PATH' '$CONFIG_DIR/backups/$server_backup_name'; fi"
    
    # Upload config file
    print_step "Uploading config file..."
    scp -i "$EC2_KEY_PATH" -o StrictHostKeyChecking=no "$LOCAL_CONFIG_FILE" "$EC2_USER@$EC2_HOST:$REMOTE_CONFIG_PATH"
    
    # Set proper permissions
    print_step "Setting permissions..."
    remote_exec "sudo chown $EC2_USER:$EC2_USER $REMOTE_CONFIG_PATH"
    remote_exec "sudo chmod 644 $REMOTE_CONFIG_PATH"
    
    print_status "Config file uploaded successfully!"
    print_status "Server backup created: $CONFIG_DIR/backups/$server_backup_name"
}

# Main script logic
case "${1:-}" in
    pull)
        shift
        pull_config
        ;;
    push)
        shift
        push_config "$1" "$@"
        ;;
    *)
        show_usage
        exit 1
        ;;
esac 