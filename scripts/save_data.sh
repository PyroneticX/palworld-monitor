#!/bin/bash

# PalWorld Dedicated Server - Save Data Management Script (Linux)
# This script manages save data between local and remote PalWorld server

set -e  # Exit on any error

# Source shared configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}" )" && pwd)"
source "$SCRIPT_DIR/config.sh"

# Save data configuration
SAVE_DIR="$PALWORLD_DIR/Pal/Saved/SaveGames"
BACKUP_DIR="./saves/backups"

# Function to show usage
show_usage() {
    echo "Usage: $0 {pull|push} world_dir [options]"
    echo ""
    echo "Commands:"
    echo "  pull     - Download save data from EC2 server"
    echo "  push     - Upload local save data to EC2 server (and update GameUserSettings.ini)"
    echo ""
    echo "Arguments:"
    echo "  world_dir  - Absolute path to world directory to push or pull (e.g., /home/user/SavedGames/1) (required)"
    echo ""
    echo "Options:"
    echo "  --backup - Create backup before operation (for push command)"
    echo "  --force  - Skip confirmation prompts"
    echo ""
    echo "Examples:"
    echo "  $0 pull /home/user/SavedGames/1                    # Download SavedGames/1 from server to this path"
    echo "  $0 push /home/user/SavedGames/1                    # Push /home/user/SavedGames/1 to server as SavedGames/0"
    echo "  $0 push /home/user/SavedGames/2 --backup           # Create backup before pushing"
    echo "  $0 push /home/user/SavedGames/3 --force            # Skip confirmation prompts"
    echo ""
    echo "Note: The push command will copy the specified world directory to SavedGames/0"
    echo "      on the server and update GameUserSettings.ini with the world name."
}

# Function to create backup
create_backup() {
    local backup_name="backup_$(date +%Y%m%d_%H%M%S)"
    local backup_path="$BACKUP_DIR/$backup_name"
    
    print_status "Creating backup: $backup_path"
    mkdir -p "$BACKUP_DIR"
    
    if [ -d "$world_dir" ]; then
        cp -r "$world_dir" "$backup_path"
        print_status "Backup created: $backup_path"
    else
        print_warning "No local saves to backup"
    fi
}

# Function to update GameUserSettings.ini with save folder name
update_game_settings() {
    local save_folder_name="$1"
    
    if [ -z "$save_folder_name" ]; then
        print_error "Save folder name is required"
        exit 1
    fi
    
    print_step "Updating GameUserSettings.ini with save folder name..."
    
    # Path to GameUserSettings.ini
    local game_settings_file="$PALWORLD_DIR/Pal/Saved/Config/LinuxServer/GameUserSettings.ini"
    
    # Check if GameUserSettings.ini exists
    if ! remote_exec "test -f $game_settings_file"; then
        print_error "GameUserSettings.ini not found: $game_settings_file"
        print_error "Make sure PalWorld server is properly installed"
        exit 1
    fi
    
    # Create backup of GameUserSettings.ini
    print_step "Creating backup of GameUserSettings.ini..."
    remote_exec "sudo cp $game_settings_file $game_settings_file.backup.$(date +%Y%m%d_%H%M%S)"
    
    # Update DedicatedServerName using sed
    print_step "Updating DedicatedServerName to: $save_folder_name"
    remote_exec "sudo sed -i 's/DedicatedServerName=.*/DedicatedServerName=$save_folder_name/g' $game_settings_file"
    
    # Verify the change
    print_step "Verifying the change..."
    remote_exec "grep 'DedicatedServerName=' $game_settings_file"
    
    print_status "GameUserSettings.ini updated successfully!"
}

# Function to pull save data from server
pull_saves() {
    world_dir="$1"
    
    # Check if world directory is provided
    if [ -z "$world_dir" ]; then
        print_error "World directory is required"
        show_usage
        exit 1
    fi
    
    # Extract world name from absolute path
    world_name="$(basename "$world_dir")"
    
    # Check if key file exists
    if [ ! -f "$EC2_KEY_PATH" ]; then
        print_error "EC2 key file not found: $EC2_KEY_PATH"
        exit 1
    fi
    
    # Check if save directory exists on server
    print_step "Checking save directory on server..."
    if ! remote_exec "test -d $SAVE_DIR/$world_name"; then
        print_error "Save directory not found on server: $SAVE_DIR/$world_name"
        print_error "Make sure PalWorld server is properly installed"
        exit 1
    fi
    
    # Create local world directory if needed
    mkdir -p "$world_dir"
    
    # Download save data
    print_step "Downloading save data..."
    scp -i "$EC2_KEY_PATH" -o StrictHostKeyChecking=no -r "$EC2_USER@$EC2_HOST:$SAVE_DIR/$world_name/" "$world_dir/"
    
    print_status "Save data downloaded successfully!"
    print_status "Local save directory: $world_dir"
}

# Function to push save data to server
push_saves() {
    world_dir="$1"
    local force=false
    local create_backup_flag=false
    
    # Check if world directory is provided
    if [ -z "$world_dir" ]; then
        print_error "World directory is required"
        show_usage
        exit 1
    fi
    
    # Check if the specified world directory exists locally
    if [ ! -d "$world_dir" ]; then
        print_error "World directory not found: $world_dir"
        print_error "Make sure the world directory exists"
        exit 1
    fi
    
    # Extract world name from absolute path
    world_name="$(basename "$world_dir")"
    
    # Parse options (skip first argument)
    shift
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
    
    print_status "Pushing save data to EC2 server..."
    
    # Check if key file exists
    if [ ! -f "$EC2_KEY_PATH" ]; then
        print_error "EC2 key file not found: $EC2_KEY_PATH"
        exit 1
    fi
    
    # Create backup if requested
    if [ "$create_backup_flag" = true ]; then
        create_backup
    fi
    
    # Confirm operation unless --force is used
    if [ "$force" = false ]; then
        echo ""
        print_warning "This will replace the active save data on the server!"
        print_warning "World directory '$world_dir' will be copied to SavedGames/0"
        print_warning "Make sure the PalWorld server is stopped before pushing saves."
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
        print_warning "It's recommended to stop the server before pushing saves."
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
    remote_exec "sudo mkdir -p $SAVE_DIR/backups"
    remote_exec "sudo chown $EC2_USER:$EC2_USER $SAVE_DIR/backups"
    
    # Create server backup
    local server_backup_name="server_backup_$(date +%Y%m%d_%H%M%S)"
    remote_exec "if [ -d '$SAVE_DIR' ] && [ \"\$(ls -A '$SAVE_DIR' 2>/dev/null)\" ]; then cp -r '$SAVE_DIR' '$SAVE_DIR/backups/$server_backup_name'; fi"
    
    # Upload the specific world directory to SavedGames/0/[world_id] on server
    # Ensure the target directory exists
    remote_exec "sudo mkdir -p $SAVE_DIR/0/$world_name && sudo chown $EC2_USER:$EC2_USER $SAVE_DIR/0/$world_name"

    # Copy contents of world_dir into SavedGames/0/[world_id]
    print_step "Uploading world directory '$world_dir' to SavedGames/0/$world_name/ ..."
    scp -i "$EC2_KEY_PATH" -o StrictHostKeyChecking=no -r "$world_dir"/* "$EC2_USER@$EC2_HOST:$SAVE_DIR/0/$world_name/"
    
    # Set proper permissions
    print_step "Setting permissions..."
    remote_exec "sudo chown -R $EC2_USER:$EC2_USER $SAVE_DIR"
    remote_exec "sudo chmod -R 755 $SAVE_DIR"
    
    # Update GameUserSettings.ini with world name
    if [ -n "$world_name" ]; then
        update_game_settings "$world_name"
    else
        print_warning "Could not extract world name from path, skipping GameUserSettings.ini update"
    fi
    
    print_status "Save data uploaded successfully!"
    print_status "World directory '$world_dir' copied to SavedGames/0"
    print_status "Server backup created: $SAVE_DIR/backups/$server_backup_name"
}

# Main script logic
case "${1:-}" in
    pull)
        shift
        pull_saves "$1"
        ;;
    push)
        shift
        push_saves "$1" "$@"
        ;;
    *)
        show_usage
        exit 1
        ;;
esac 