#!/bin/bash

# Shared Configuration for PalWorld Server Management Scripts
# This file reads configuration from config.json and provides common functions

# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CONFIG_FILE="$SCRIPT_DIR/config.json"

# Function to read JSON values using jq (if available) or grep/sed fallback
get_config_value() {
    local key="$1"
    local value
    
    if command -v jq >/dev/null 2>&1; then
        value=$(jq -r "$key" "$CONFIG_FILE" 2>/dev/null)
    else
        # Fallback using grep and sed
        case "$key" in
            ".ec2.host")
                value=$(grep '"host"' "$CONFIG_FILE" | sed 's/.*"host":\s*"\([^"]*\)".*/\1/')
                ;;
            ".ec2.user")
                value=$(grep '"user"' "$CONFIG_FILE" | sed 's/.*"user":\s*"\([^"]*\)".*/\1/')
                ;;
            ".ec2.key_path")
                value=$(grep '"key_path"' "$CONFIG_FILE" | sed 's/.*"key_path":\s*"\([^"]*\)".*/\1/')
                ;;
            ".palworld.dir")
                value=$(grep '"dir"' "$CONFIG_FILE" | sed 's/.*"dir":\s*"\([^"]*\)".*/\1/')
                ;;
            ".palworld.steamcmd_dir")
                value=$(grep '"steamcmd_dir"' "$CONFIG_FILE" | sed 's/.*"steamcmd_dir":\s*"\([^"]*\)".*/\1/')
                ;;
            ".palworld.remote_dir")
                value=$(grep '"remote_dir"' "$CONFIG_FILE" | sed 's/.*"remote_dir":\s*"\([^"]*\)".*/\1/')
                ;;
            ".palworld.app_id")
                value=$(grep '"app_id"' "$CONFIG_FILE" | sed 's/.*"app_id":\s*"\([^"]*\)".*/\1/')
                ;;
        esac
    fi
    
    echo "$value"
}

# Load configuration from JSON
EC2_HOST=$(get_config_value ".ec2.host")
EC2_USER=$(get_config_value ".ec2.user")
EC2_KEY_PATH=$(get_config_value ".ec2.key_path")
PALWORLD_DIR=$(get_config_value ".palworld.dir")
STEAMCMD_DIR=$(get_config_value ".palworld.steamcmd_dir")
REMOTE_DIR=$(get_config_value ".palworld.remote_dir")
PALWORLD_APP_ID=$(get_config_value ".palworld.app_id")

# Colors for output (Linux/macOS)
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output (Linux/macOS)
print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

print_step() {
    echo -e "${BLUE}[STEP]${NC} $1"
}

# Function to execute remote command
remote_exec() {
    local cmd="$1"
    ssh -i "$EC2_KEY_PATH" -o StrictHostKeyChecking=no "$EC2_USER@$EC2_HOST" "$cmd"
}

# Function to check if service is running
check_service_status() {
    local service_name="$1"
    remote_exec "systemctl is-active --quiet $service_name"
    return $?
}

# Function to validate configuration
validate_config() {
    if [ ! -f "$CONFIG_FILE" ]; then
        print_error "Configuration file not found: $CONFIG_FILE"
        return 1
    fi

    if [ "$EC2_HOST" = "your-ec2-instance-ip-or-domain" ] || [ -z "$EC2_HOST" ]; then
        print_error "Please update the EC2_HOST variable in config.json with your EC2 instance IP or domain"
        return 1
    fi

    if [ "$EC2_KEY_PATH" = "~/.ssh/your-key.pem" ] || [ -z "$EC2_KEY_PATH" ]; then
        print_error "Please update the EC2_KEY_PATH variable in config.json with your EC2 key file path"
        return 1
    fi

    # Expand the key path
    EC2_KEY_PATH=$(eval echo $EC2_KEY_PATH)

    # Check if key file exists
    if [ ! -f "$EC2_KEY_PATH" ]; then
        print_error "EC2 key file not found: $EC2_KEY_PATH"
        return 1
    fi

    return 0
} 