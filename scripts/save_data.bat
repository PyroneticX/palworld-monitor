@echo off
REM PalWorld Dedicated Server - Save Data Management Script (Windows)
REM This script manages save data between local and remote PalWorld server

setlocal enabledelayedexpansion

REM Source shared configuration
set SCRIPT_DIR=%~dp0
call "%SCRIPT_DIR%config.bat"

REM Save data configuration
set SAVE_DIR=%PALWORLD_DIR%/Pal/Saved/SaveGames
set BACKUP_DIR=./saves/backups

REM Jump to main logic
goto :main

REM Function to show usage
:show_usage
echo Usage: %0 {pull^|push} world_dir [options]
echo.
echo Commands:
echo   pull     - Download save data from EC2 server
echo   push     - Upload local save data to EC2 server ^(and update GameUserSettings.ini^)
echo.
echo Arguments:
echo   world_dir  - Absolute path to world directory to push or pull ^(e.g., C:\path\to\SavedGames\1^) ^(required^)
echo.
echo Options:
echo   --backup - Create backup before operation ^(for push command^)
echo   --force  - Skip confirmation prompts
echo.
echo Examples:
echo   %0 pull C:\path\to\SavedGames\1                    # Download SavedGames/1 from server to this path
echo   %0 push C:\path\to\SavedGames\1                    # Push C:\path\to\SavedGames\1 to server as SavedGames/0
echo   %0 push C:\path\to\SavedGames\2 --backup           # Create backup before pushing
echo   %0 push C:\path\to\SavedGames\3 --force            # Skip confirmation prompts
echo.
echo Note: The push command will copy the specified world directory to SavedGames/0
echo       on the server and update GameUserSettings.ini with the world name.
goto :eof

REM Function to create backup
:create_backup
set backup_name=backup_%date:~-4,4%%date:~-10,2%%date:~-7,2%_%time:~0,2%%time:~3,2%%time:~6,2%
set backup_name=!backup_name: =0!
set backup_path=%BACKUP_DIR%\!backup_name!

echo [INFO] Creating backup: !backup_path!
if not exist "%BACKUP_DIR%" mkdir "%BACKUP_DIR%"

if exist "%world_dir%" (
    xcopy "%world_dir%" "!backup_path!" /E /I /Y >nul
    echo [INFO] Backup created: !backup_path!
) else (
    echo [WARNING] No local saves to backup
)
goto :eof

REM Function to pull save data from server
:pull_saves
set world_dir=%1

REM Check if world directory is provided
if "%world_dir%"=="" (
    echo [ERROR] World directory is required
    call :show_usage
    exit /b 1
)

REM Check if key file exists
if not exist "%EC2_KEY_PATH%" (
    echo [ERROR] EC2 key file not found: %EC2_KEY_PATH%
    exit /b 1
)

REM Extract world name from absolute path
for %%i in ("%world_dir%") do set "world_name=%%~nxi"

REM Check if save directory exists on server
echo [STEP] Checking save directory on server...
ssh -i "%EC2_KEY_PATH%" %SSH_OPTS% %EC2_USER%@%EC2_HOST% "test -d %SAVE_DIR%/!world_name!"
if errorlevel 1 (
    echo [ERROR] Save directory not found on server: %SAVE_DIR%/!world_name!
    echo [ERROR] Make sure PalWorld server is properly installed
    echo [HELP] Run the test_ssh_connection.bat script to diagnose connection issues
    exit /b 1
)

REM Create local world directory if needed
if not exist "%world_dir%" mkdir "%world_dir%"

REM Download save data
echo [STEP] Downloading save data...
scp -i "%EC2_KEY_PATH%" %SCP_OPTS% -r %EC2_USER%@%EC2_HOST%:%SAVE_DIR%/!world_name!/ "%world_dir%/"

echo [INFO] Save data downloaded successfully!
echo [INFO] Local save directory: %world_dir%
goto :eof

REM Function to update GameUserSettings.ini with save folder name
:update_game_settings
set save_folder_name=%1

if "%save_folder_name%"=="" (
    echo [ERROR] Save folder name is required
    exit /b 1
)

echo [STEP] Updating GameUserSettings.ini with save folder name...

REM Path to GameUserSettings.ini
set GAME_SETTINGS_FILE=%PALWORLD_DIR%/Pal/Saved/Config/LinuxServer/GameUserSettings.ini

REM Check if GameUserSettings.ini exists
ssh -i "%EC2_KEY_PATH%" %SSH_OPTS% %EC2_USER%@%EC2_HOST% "test -f %GAME_SETTINGS_FILE%"
if errorlevel 1 (
    echo [ERROR] GameUserSettings.ini not found: %GAME_SETTINGS_FILE%
    echo [ERROR] Make sure PalWorld server is properly installed
    exit /b 1
)

REM Create backup of GameUserSettings.ini
echo [STEP] Creating backup of GameUserSettings.ini...
ssh -i "%EC2_KEY_PATH%" %SSH_OPTS% %EC2_USER%@%EC2_HOST% "sudo cp %GAME_SETTINGS_FILE% %GAME_SETTINGS_FILE%.backup.$(date +%%Y%%m%%d_%%H%%M%%S)"

REM Update DedicatedServerName using sed
echo [STEP] Updating DedicatedServerName to: %save_folder_name%
ssh -i "%EC2_KEY_PATH%" %SSH_OPTS% %EC2_USER%@%EC2_HOST% "sudo sed -i 's/DedicatedServerName=.*/DedicatedServerName=%save_folder_name%/g' %GAME_SETTINGS_FILE%"

REM Verify the change
echo [STEP] Verifying the change...
ssh -i "%EC2_KEY_PATH%" %SSH_OPTS% %EC2_USER%@%EC2_HOST% "grep 'DedicatedServerName=' %GAME_SETTINGS_FILE%"

echo [INFO] GameUserSettings.ini updated successfully!
goto :eof

REM Function to push save data to server
:push_saves
set world_dir=%1
set force=false
set create_backup_flag=false

REM Check if world directory is provided
if "%world_dir%"=="" (
    echo [ERROR] World directory is required
    call :show_usage
    exit /b 1
)

REM Check if the specified world directory exists locally
if not exist "%world_dir%" (
    echo [ERROR] World directory not found: %world_dir%
    echo [ERROR] Make sure the world directory exists
    exit /b 1
)

REM Extract world name from absolute path
for %%i in ("%world_dir%") do set "world_name=%%~nxi"

REM Skip the first argument (world_dir) and parse remaining options
shift

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
if "%1"=="pull" goto :pull_saves
if "%1"=="push" (
    shift
    goto :parse_options
)
echo Unknown option: %1
call :show_usage
exit /b 1

:push_main
echo [INFO] Pushing save data to EC2 server...

REM Check if key file exists
if not exist "%EC2_KEY_PATH%" (
    echo [ERROR] EC2 key file not found: %EC2_KEY_PATH%
    exit /b 1
)

REM Create backup if requested
if "%create_backup_flag%"=="true" (
    call :create_backup
)

REM Confirm operation unless --force is used
if "%force%"=="false" (
    echo.
    echo [WARNING] This will replace the active save data on the server!
    echo [WARNING] World directory '%world_dir%' will be copied to SavedGames/0
    echo [WARNING] Make sure the PalWorld server is stopped before pushing saves.
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
    echo [WARNING] It's recommended to stop the server before pushing saves.
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
ssh -i "%EC2_KEY_PATH%" %SSH_OPTS% %EC2_USER%@%EC2_HOST% "sudo mkdir -p %SAVE_DIR%/backups"
ssh -i "%EC2_KEY_PATH%" %SSH_OPTS% %EC2_USER%@%EC2_HOST% "sudo chown %EC2_USER%:%EC2_USER% %SAVE_DIR%/backups"

REM Create server backup
set server_backup_name=server_backup_%date:~-4,4%%date:~-10,2%%date:~-7,2%_%time:~0,2%%time:~3,2%%time:~6,2%
set server_backup_name=!server_backup_name: =0!
ssh -i "%EC2_KEY_PATH%" %SSH_OPTS% %EC2_USER%@%EC2_HOST% "if [ -d '%SAVE_DIR%' ] && [ \"$(ls -A '%SAVE_DIR%' 2>/dev/null)\" ]; then cp -r '%SAVE_DIR%' '%SAVE_DIR%/backups/!server_backup_name!'; fi"

REM Upload the specific world directory to SavedGames/0/[world_id] on server
REM Ensure the target directory exists
ssh -i "%EC2_KEY_PATH%" %SSH_OPTS% %EC2_USER%@%EC2_HOST% "sudo mkdir -p %SAVE_DIR%/0/!world_name! && sudo chown %EC2_USER%:%EC2_USER% %SAVE_DIR%/0/!world_name!"

REM Copy contents of world_dir into SavedGames/0/[world_id]
echo [STEP] Uploading world directory '%world_dir%' to SavedGames/0/!world_name!/ ...
scp -i "%EC2_KEY_PATH%" %SCP_OPTS% -r "%world_dir%/*" %EC2_USER%@%EC2_HOST%:%SAVE_DIR%/0/!world_name!/ 

REM Set proper permissions
echo [STEP] Setting permissions...
ssh -i "%EC2_KEY_PATH%" %SSH_OPTS% %EC2_USER%@%EC2_HOST% "sudo chown -R %EC2_USER%:%EC2_USER% %SAVE_DIR%"
ssh -i "%EC2_KEY_PATH%" %SSH_OPTS% %EC2_USER%@%EC2_HOST% "sudo chmod -R 755 %SAVE_DIR%"

REM Update GameUserSettings.ini with world name
if not "%world_name%"=="" (
    call :update_game_settings !world_name!
) else (
    echo [WARNING] Could not extract world name from path, skipping GameUserSettings.ini update
)

echo [INFO] Save data uploaded successfully!
echo [INFO] World directory '%world_dir%' copied to SavedGames/0
echo [INFO] Server backup created: %SAVE_DIR%/backups/!server_backup_name!
goto :eof

REM Main script logic
:main
if "%1"=="" goto :show_usage
if "%1"=="pull" (
    shift
    goto :pull_saves
)
if "%1"=="push" (
    shift
    goto :push_saves
)
goto :show_usage 