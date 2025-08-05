@echo off
REM Shared Configuration for PalWorld Server Management Scripts (Windows)
REM This file reads configuration from config.json and provides common functions

REM Get the directory where this script is located
set SCRIPT_DIR=%~dp0
set CONFIG_FILE=%SCRIPT_DIR%config.json

REM Load configuration from JSON using PowerShell
for /f "delims=" %%i in ('powershell -Command "& {$config = Get-Content '%CONFIG_FILE%' | ConvertFrom-Json; $config.ec2.host}" 2^>nul') do set EC2_HOST=%%i
for /f "delims=" %%i in ('powershell -Command "& {$config = Get-Content '%CONFIG_FILE%' | ConvertFrom-Json; $config.ec2.user}" 2^>nul') do set EC2_USER=%%i
for /f "delims=" %%i in ('powershell -Command "& {$config = Get-Content '%CONFIG_FILE%' | ConvertFrom-Json; $config.ec2.key_path}" 2^>nul') do set EC2_KEY_PATH=%%i
for /f "delims=" %%i in ('powershell -Command "& {$config = Get-Content '%CONFIG_FILE%' | ConvertFrom-Json; $config.palworld.dir}" 2^>nul') do set PALWORLD_DIR=%%i
for /f "delims=" %%i in ('powershell -Command "& {$config = Get-Content '%CONFIG_FILE%' | ConvertFrom-Json; $config.palworld.steamcmd_dir}" 2^>nul') do set STEAMCMD_DIR=%%i
for /f "delims=" %%i in ('powershell -Command "& {$config = Get-Content '%CONFIG_FILE%' | ConvertFrom-Json; $config.palworld.remote_dir}" 2^>nul') do set REMOTE_DIR=%%i
for /f "delims=" %%i in ('powershell -Command "& {$config = Get-Content '%CONFIG_FILE%' | ConvertFrom-Json; $config.palworld.app_id}" 2^>nul') do set PALWORLD_APP_ID=%%i

REM Validate configuration
call :validate_config
:validate_config
if not exist "%CONFIG_FILE%" (
    echo [ERROR] Configuration file not found: %CONFIG_FILE%
    exit /b 1
)

if "%EC2_HOST%"=="your-ec2-instance-ip-or-domain" (
    echo [ERROR] Please update the EC2_HOST variable in config.json with your EC2 instance IP or domain
    exit /b 1
)

if "%EC2_KEY_PATH%"=="~/.ssh/your-key.pem" (
    echo [ERROR] Please update the EC2_KEY_PATH variable in config.json with your EC2 key file path
    exit /b 1
)

REM Expand the key path (handle tilde)
if "%EC2_KEY_PATH:~0,1%"=="~" (
    set EC2_KEY_PATH=%USERPROFILE%%EC2_KEY_PATH:~1%
)

REM Check if key file exists
if not exist "%EC2_KEY_PATH%" (
    echo [ERROR] EC2 key file not found: %EC2_KEY_PATH%
    echo [HELP] Please check the key_path in config.json
    echo [HELP] Use absolute path or relative path from scripts directory
    echo [HELP] Example: "C:\\Users\\YourUser\\.ssh\\key.pem" or "..\\keys\\key.pem"
    exit /b 1
)

REM Set SSH connection parameters for better reliability
set SSH_OPTS=-o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null -o ConnectTimeout=30 -o ServerAliveInterval=60 -o ServerAliveCountMax=3
set SCP_OPTS=-o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null -o ConnectTimeout=30

exit /b 0 