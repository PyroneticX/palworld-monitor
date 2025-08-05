@echo off
REM PalWorld Server Update Script for EC2 (Windows)
REM This script updates the PalWorld server on an AWS EC2 instance

REM Source shared configuration
for /f "tokens=*" %%a in ('powershell -Command "Split-Path -Parent $PSCommandPath"') do set SCRIPT_DIR=%%a
call "%SCRIPT_DIR%\config.bat"

echo [INFO] Starting PalWorld server update on EC2 instance: %EC2_HOST%

REM Validate configuration
call :validate_config
if %ERRORLEVEL% NEQ 0 exit /b 1

echo [STEP] Checking if PalWorld server is running...
ssh -i "%EC2_KEY_PATH%" -o StrictHostKeyChecking=no "%EC2_USER%@%EC2_HOST%" "systemctl is-active --quiet palworld-server"
if %ERRORLEVEL% EQU 0 (
    echo [INFO] Stopping PalWorld server...
    ssh -i "%EC2_KEY_PATH%" -o StrictHostKeyChecking=no "%EC2_USER%@%EC2_HOST%" "sudo systemctl stop palworld-server"
    timeout /t 5 /nobreak >nul
) else (
    echo [WARNING] PalWorld server service not found or not running
)

echo [STEP] Checking SteamCMD installation...
ssh -i "%EC2_KEY_PATH%" -o StrictHostKeyChecking=no "%EC2_USER%@%EC2_HOST%" "test -d %STEAMCMD_DIR%"
if %ERRORLEVEL% NEQ 0 (
    echo [INFO] Installing SteamCMD...
    ssh -i "%EC2_KEY_PATH%" -o StrictHostKeyChecking=no "%EC2_USER%@%EC2_HOST%" "sudo mkdir -p %STEAMCMD_DIR% && cd %STEAMCMD_DIR% && wget -qO- 'https://steamcdn-a.akamaihd.net/client/installer/steamcmd_linux.tar.gz' | tar -xz"
    ssh -i "%EC2_KEY_PATH%" -o StrictHostKeyChecking=no "%EC2_USER%@%EC2_HOST%" "sudo chown -R %EC2_USER%:%EC2_USER% %STEAMCMD_DIR%"
) else (
    echo [INFO] SteamCMD already installed
)

echo [STEP] Updating SteamCMD...
ssh -i "%EC2_KEY_PATH%" -o StrictHostKeyChecking=no "%EC2_USER%@%EC2_HOST%" "cd %STEAMCMD_DIR% && ./steamcmd.sh +quit"

echo [STEP] Ensuring PalWorld server directory exists...
ssh -i "%EC2_KEY_PATH%" -o StrictHostKeyChecking=no "%EC2_USER%@%EC2_HOST%" "sudo mkdir -p %PALWORLD_DIR% && sudo chown -R %EC2_USER%:%EC2_USER% %PALWORLD_DIR%"

echo [STEP] Updating PalWorld server...
ssh -i "%EC2_KEY_PATH%" -o StrictHostKeyChecking=no "%EC2_USER%@%EC2_HOST%" "cd %STEAMCMD_DIR% && ./steamcmd.sh +login anonymous +force_install_dir %PALWORLD_DIR% +app_update %PALWORLD_APP_ID% validate +quit"

echo [INFO] Setting proper permissions...
ssh -i "%EC2_KEY_PATH%" -o StrictHostKeyChecking=no "%EC2_USER%@%EC2_HOST%" "sudo chown -R %EC2_USER%:%EC2_USER% %PALWORLD_DIR%"
ssh -i "%EC2_KEY_PATH%" -o StrictHostKeyChecking=no "%EC2_USER%@%EC2_HOST%" "chmod +x %PALWORLD_DIR%/PalServer.sh"

echo [STEP] Setting up systemd service...
call "%SCRIPT_DIR%\create_systemd_service.bat"

echo [STEP] Starting PalWorld server...
ssh -i "%EC2_KEY_PATH%" -o StrictHostKeyChecking=no "%EC2_USER%@%EC2_HOST%" "sudo systemctl start palworld-server"

REM Wait a moment and check status
timeout /t 10 /nobreak >nul
echo [STEP] Checking server status...
ssh -i "%EC2_KEY_PATH%" -o StrictHostKeyChecking=no "%EC2_USER%@%EC2_HOST%" "systemctl is-active --quiet palworld-server"
if %ERRORLEVEL% EQU 0 (
    echo [INFO] PalWorld server started successfully!
    ssh -i "%EC2_KEY_PATH%" -o StrictHostKeyChecking=no "%EC2_USER%@%EC2_HOST%" "sudo systemctl status palworld-server --no-pager -l"
) else (
    echo [ERROR] Failed to start PalWorld server
    ssh -i "%EC2_KEY_PATH%" -o StrictHostKeyChecking=no "%EC2_USER%@%EC2_HOST%" "sudo journalctl -u palworld-server --no-pager -l -n 20"
    exit /b 1
)

echo [INFO] PalWorld server update completed successfully!
echo [INFO] Server directory: %PALWORLD_DIR%
echo [INFO] You can check server logs with: ssh %EC2_USER%@%EC2_HOST% 'sudo journalctl -u palworld-server -f' 