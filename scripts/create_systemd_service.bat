@echo off
REM PalWorld SystemD Service Creation Script (Windows)
REM This script creates and configures the systemd service for PalWorld server

REM Source shared configuration
set SCRIPT_DIR=%~dp0
call %SCRIPT_DIR%config.bat

echo [INFO] Creating systemd service for PalWorld server...

REM Check if systemd service already exists
echo [STEP] Checking if systemd service already exists...
ssh -i "%EC2_KEY_PATH%" -o StrictHostKeyChecking=no "%EC2_USER%@%EC2_HOST%" "test -f /etc/systemd/system/palworld-control.service"
if %ERRORLEVEL% EQU 0 (
    echo [INFO] Systemd service already exists - will override it
    echo [INFO] Current service configuration:
    ssh -i "%EC2_KEY_PATH%" -o StrictHostKeyChecking=no "%EC2_USER%@%EC2_HOST%" "sudo cat /etc/systemd/system/palworld-control.service"
    echo.
)

REM Upload the service file to the remote server
echo [STEP] Uploading service configuration...
scp -i "%EC2_KEY_PATH%" -o StrictHostKeyChecking=no "%SCRIPT_DIR%palworld-control.service" "%EC2_USER%@%EC2_HOST%:/tmp/palworld-control.service"

REM Move the file to the correct location and set permissions
ssh -i "%EC2_KEY_PATH%" -o StrictHostKeyChecking=no "%EC2_USER%@%EC2_HOST%" "sudo mv /tmp/palworld-control.service /etc/systemd/system/palworld-control.service && sudo chmod 644 /etc/systemd/system/palworld-control.service"

REM Reload systemd daemon
echo [STEP] Reloading systemd daemon...
ssh -i "%EC2_KEY_PATH%" -o StrictHostKeyChecking=no "%EC2_USER%@%EC2_HOST%" "sudo systemctl daemon-reload"

REM Enable the service
echo [STEP] Enabling PalWorld control service...
ssh -i "%EC2_KEY_PATH%" -o StrictHostKeyChecking=no "%EC2_USER%@%EC2_HOST%" "sudo systemctl enable palworld-control"

echo [INFO] Systemd service created and enabled successfully!
echo [INFO] Service file location: /etc/systemd/system/palworld-control.service

REM Show the created service configuration
echo [INFO] Service configuration:
ssh -i "%EC2_KEY_PATH%" -o StrictHostKeyChecking=no "%EC2_USER%@%EC2_HOST%" "sudo cat /etc/systemd/system/palworld-control.service"

echo [INFO] You can now manage the service with:
echo [INFO]   sudo systemctl start palworld-control
echo [INFO]   sudo systemctl stop palworld-control
echo [INFO]   sudo systemctl restart palworld-control
echo [INFO]   sudo systemctl status palworld-control 