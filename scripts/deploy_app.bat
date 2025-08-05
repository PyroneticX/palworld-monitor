@echo off
setlocal enabledelayedexpansion
REM PalWorld Dedicated Server Auto Start/Stop - EC2 Deployment Script (Windows)
REM This script deploys the application to an AWS EC2 instance

REM Get the directory where this script is located and navigate to project root
set SCRIPT_DIR=%~dp0
set PROJECT_ROOT=%SCRIPT_DIR%..
cd /d "%PROJECT_ROOT%"

REM Source shared configuration
call "%SCRIPT_DIR%config.bat"

echo [INFO] Starting deployment to EC2 instance: %EC2_HOST%

REM Create remote directory if it doesn't exist
echo [INFO] Creating remote directory: %REMOTE_DIR%
ssh -i "%EC2_KEY_PATH%" -o StrictHostKeyChecking=no "%EC2_USER%@%EC2_HOST%" "sudo mkdir -p %REMOTE_DIR% && sudo chown %EC2_USER%:%EC2_USER% %REMOTE_DIR%"

REM Deploy application files
echo [INFO] Deploying application files...

REM Create a temporary directory for files to deploy
set TEMP_DIR=%TEMP%\palworld-deploy-%RANDOM%
mkdir "%TEMP_DIR%"

REM Copy essential files to temp directory (excluding .json files)
robocopy src "%TEMP_DIR%\src" /E /XF *.json /NFL /NDL /NJH /NJS /NC /NS /NP >nul 2>&1

copy requirements.txt "%TEMP_DIR%\"
copy README.md "%TEMP_DIR%\"
copy LICENSE "%TEMP_DIR%\"

REM Copy images directory if it exists (excluding .json files)
if exist images (
    robocopy images "%TEMP_DIR%\images" /E /XF *.json /NFL /NDL /NJH /NJS /NC /NS /NP >nul 2>&1
)

REM Copy data directory if it exists (excluding all .json files)
if exist data (
    mkdir "%TEMP_DIR%\data"
    REM Copy data files but exclude all .json files
    for /r data %%f in (*) do (
        if not "%%~xf"==".json" (
            set "relpath=%%f"
            set "relpath=!relpath:%cd%\data\=!"
            if not "!relpath!"=="" (
                if not exist "%TEMP_DIR%\data\!relpath!" (
                    mkdir "%TEMP_DIR%\data\!relpath!" 2>nul
                )
                copy "%%f" "%TEMP_DIR%\data\!relpath!" >nul
            )
        )
    )
)

REM Deploy files to EC2
scp -i "%EC2_KEY_PATH%" -o StrictHostKeyChecking=no -r "%TEMP_DIR%\*" "%EC2_USER%@%EC2_HOST%:%REMOTE_DIR%/"

REM Clean up temp directory
rmdir /S /Q "%TEMP_DIR%"

echo [INFO] Deployment completed successfully!

REM Initialize virtual environment and install Python dependencies on the remote server
echo [INFO] Setting up Python virtual environment and installing dependencies...
ssh -i "%EC2_KEY_PATH%" -o StrictHostKeyChecking=no "%EC2_USER%@%EC2_HOST%" "cd %REMOTE_DIR% && if [ ! -d 'venv' ]; then python3 -m venv venv; fi && venv/bin/pip install -r requirements.txt"
if %ERRORLEVEL% EQU 0 (
    echo [INFO] Dependencies installed successfully!
) else (
    echo [WARNING] Failed to install dependencies automatically.
    echo [INFO] You may need to install Python and pip manually on the remote server.
    echo [INFO] Common commands: sudo apt-get install python3 python3-pip (Ubuntu/Debian)
    echo [INFO] Or: sudo yum install python3 python3-pip (CentOS/RHEL)
)

echo [INFO] Deployment to EC2 completed!
echo [INFO] Remote directory: %REMOTE_DIR%
echo [INFO] You can now SSH into your EC2 instance and run the application from %REMOTE_DIR% 