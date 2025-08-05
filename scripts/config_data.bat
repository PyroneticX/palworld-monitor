@echo off
REM PalWorld Dedicated Server - Config Data Management Script (Windows)
REM This script manages PalWorld server configuration files between local and remote server

setlocal enabledelayedexpansion

REM Source shared configuration
set SCRIPT_DIR=%~dp0
call "%SCRIPT_DIR%config.bat"

REM Config data configuration
set CONFIG_DIR=%PALWORLD_DIR%/Pal/Saved/Config/WindowsServer
set CONFIG_FILE=PalWorldSettings.ini
set REMOTE_CONFIG_PATH=%CONFIG_DIR%/%CONFIG_FILE%

REM Function to show usage
:show_usage
echo Usage: %0 {pull^|push} [file_path] [options]
echo.
echo Commands:
echo   pull     - Download PalWorld config from EC2 server to current directory
echo   push     - Upload local PalWorld config file to EC2 server
echo.
echo Arguments:
echo   file_path - Path to config file ^(required for push command^)
echo.
echo Options:
echo   --backup - Create backup before operation ^(for push command^)
echo   --force  - Skip confirmation prompts
echo.
echo Examples:
echo   %0 pull                    # Download config to current directory
echo   %0 push C:\path\to\config.ini # Upload config file to server
echo   %0 push config.ini --backup # Create backup before pushing
echo   %0 push config.ini --force  # Skip confirmation prompts
goto :eof

REM Function to create backup
:create_backup
set backup_name=config_backup_%date:~-4,4%%date:~-10,2%%date:~-7,2%_%time:~0,2%%time:~3,2%%time:~6,2%
set backup_name=!backup_name: =0!
set backup_path=%BACKUP_DIR%\!backup_name!

echo [INFO] Creating backup: !backup_path!
if not exist "%BACKUP_DIR%" mkdir "%BACKUP_DIR%"

if exist "%LOCAL_CONFIG_FILE%" (
    copy "%LOCAL_CONFIG_FILE%" "!backup_path!" >nul
    echo [INFO] Backup created: !backup_path!
) else (
    echo [WARNING] No local config file to backup
)
goto :eof

REM Function to pull config data from server
:pull_config
REM Set local config file path to current directory
set LOCAL_CONFIG_FILE=.\%CONFIG_FILE%
set BACKUP_DIR=.\backups

echo [INFO] Pulling PalWorld config from EC2 server...

REM Check if key file exists
if not exist "%EC2_KEY_PATH%" (
    echo [ERROR] EC2 key file not found: %EC2_KEY_PATH%
    exit /b 1
)

REM Check if config directory exists on server
echo [STEP] Checking config directory on server...
ssh -i "%EC2_KEY_PATH%" %SSH_OPTS% %EC2_USER%@%EC2_HOST% "test -d %CONFIG_DIR%"
if errorlevel 1 (
    echo [ERROR] Config directory not found on server: %CONFIG_DIR%
    echo [ERROR] Make sure PalWorld server is properly installed
    echo [HELP] Run the test_ssh_connection.bat script to diagnose connection issues
    exit /b 1
)

REM Check if config file exists on server
echo [STEP] Checking config file on server...
ssh -i "%EC2_KEY_PATH%" %SSH_OPTS% %EC2_USER%@%EC2_HOST% "test -f %REMOTE_CONFIG_PATH%"
if errorlevel 1 (
    echo [ERROR] Config file not found on server: %REMOTE_CONFIG_PATH%
    echo [ERROR] Make sure PalWorld server is properly configured
    exit /b 1
)

REM Download config file
echo [STEP] Downloading config file...
scp -i "%EC2_KEY_PATH%" %SCP_OPTS% %EC2_USER%@%EC2_HOST%:%REMOTE_CONFIG_PATH% "%LOCAL_CONFIG_FILE%"

echo [INFO] Config file downloaded successfully!
echo [INFO] Local config file: %LOCAL_CONFIG_FILE%
goto :eof

REM Function to push config data to server
:push_config
set config_file=%1
set force=false
set create_backup_flag=false

REM Check if config file path is provided
if "%config_file%"=="" (
    echo [ERROR] Config file path is required for push command
    call :show_usage
    exit /b 1
)

REM Set local config file path
set LOCAL_CONFIG_FILE=%config_file%
for %%F in ("%config_file%") do set BACKUP_DIR=%%~dpFbackups

REM Parse options
:parse_options
if "%1"=="" goto :push_main
if "%1"=="--force" (
    set force=true
    shift
    goto :parse_options
)
if "%1"=="--backup" (
    set create_backup_flag=true
    shift
    goto :parse_options
)
if "%1"=="pull" goto :pull_config
if "%1"=="push" (
    shift
    goto :parse_options
)
echo Unknown option: %1
call :show_usage
exit /b 1

:push_main
echo [INFO] Pushing PalWorld config to EC2 server...

REM Check if key file exists
if not exist "%EC2_KEY_PATH%" (
    echo [ERROR] EC2 key file not found: %EC2_KEY_PATH%
    exit /b 1
)

REM Check if local config file exists
if not exist "%LOCAL_CONFIG_FILE%" (
    echo [ERROR] Local config file not found: %LOCAL_CONFIG_FILE%
    echo [ERROR] Please provide a valid path to the config file
    exit /b 1
)

REM Create backup if requested
if "%create_backup_flag%"=="true" (
    call :create_backup
)

REM Confirm operation unless --force is used
if "%force%"=="false" (
    echo.
    echo [WARNING] This will replace the PalWorld config file on the server!
    echo [WARNING] Make sure the PalWorld server is stopped before pushing config.
    echo.
    set /p confirm="Are you sure you want to continue? (y/n): "
    if /i not "!confirm!"=="y" (
        echo [INFO] Operation cancelled
        exit /b 0
    )
)

REM Check if server is running and warn user
echo [STEP] Checking server status...
ssh -i "%EC2_KEY_PATH%" %SSH_OPTS% %EC2_USER%@%EC2_HOST% "systemctl is-active --quiet palworld-server"
if not errorlevel 1 (
    echo [WARNING] PalWorld server appears to be running!
    echo [WARNING] It's recommended to stop the server before pushing config.
    if "%force%"=="false" (
        set /p confirm="Continue anyway? (y/n): "
        if /i not "!confirm!"=="y" (
            echo [INFO] Operation cancelled
            exit /b 0
        )
    )
)

REM Create backup directory on server
echo [STEP] Creating backup on server...
ssh -i "%EC2_KEY_PATH%" %SSH_OPTS% %EC2_USER%@%EC2_HOST% "sudo mkdir -p %CONFIG_DIR%/backups"
ssh -i "%EC2_KEY_PATH%" %SSH_OPTS% %EC2_USER%@%EC2_HOST% "sudo chown %EC2_USER%:%EC2_USER% %CONFIG_DIR%/backups"

REM Create server backup
set server_backup_name=server_config_backup_%date:~-4,4%%date:~-10,2%%date:~-7,2%_%time:~0,2%%time:~3,2%%time:~6,2%
set server_backup_name=!server_backup_name: =0!
ssh -i "%EC2_KEY_PATH%" %SSH_OPTS% %EC2_USER%@%EC2_HOST% "if [ -f '%REMOTE_CONFIG_PATH%' ]; then cp '%REMOTE_CONFIG_PATH%' '%CONFIG_DIR%/backups/!server_backup_name!'; fi"

REM Upload config file
echo [STEP] Uploading config file...
scp -i "%EC2_KEY_PATH%" %SCP_OPTS% "%LOCAL_CONFIG_FILE%" %EC2_USER%@%EC2_HOST%:%REMOTE_CONFIG_PATH%

REM Set proper permissions
echo [STEP] Setting permissions...
ssh -i "%EC2_KEY_PATH%" %SSH_OPTS% %EC2_USER%@%EC2_HOST% "sudo chown %EC2_USER%:%EC2_USER% %REMOTE_CONFIG_PATH%"
ssh -i "%EC2_KEY_PATH%" %SSH_OPTS% %EC2_USER%@%EC2_HOST% "sudo chmod 644 %REMOTE_CONFIG_PATH%"

echo [INFO] Config file uploaded successfully!
echo [INFO] Server backup created: %CONFIG_DIR%/backups/!server_backup_name!
goto :eof

REM Main script logic
if "%1"=="" goto :show_usage
if "%1"=="pull" (
    shift
    goto :pull_config
)
if "%1"=="push" (
    shift
    goto :push_config
)
goto :show_usage 