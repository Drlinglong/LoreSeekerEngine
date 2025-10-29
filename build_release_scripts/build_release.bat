@echo off
setlocal enabledelayedexpansion

REM =================================================================
REM LoreSeekerEngine - Portable Release Build Script
REM Version: 1.0.0
REM Assumption: This script is run from a Python environment where 'pip' is available.
REM =================================================================

echo [INFO] =================================================================
echo [INFO] LoreSeekerEngine - Portable Release Build Script
echo [INFO] =================================================================
echo.

REM --- Step 1: Initialization ---
set "SCRIPT_DIR=%~dp0"
set "PROJECT_ROOT=%SCRIPT_DIR%..\..\"

set "PROJECT_NAME=LoreSeekerEngine"
set "VERSION=1.0.0"
set "RELEASE_DIR=%PROJECT_ROOT%\%PROJECT_NAME%_%VERSION%"
set "RELEASE_DIR_NAME=%PROJECT_NAME%_%VERSION%"

echo [INFO] Verifying execution environment...
echo [INFO] Project Root detected as: %PROJECT_ROOT%
echo [INFO] Release will be built in: %RELEASE_DIR%
echo.

REM --- Step 2: Cleanup ---
echo [INFO] Cleaning up previous build...
if exist "%RELEASE_DIR%" (
    rd /s /q "%RELEASE_DIR%"
    echo [INFO] Old release directory removed.
)
if exist "%PROJECT_ROOT%\%RELEASE_DIR_NAME%.zip" (
    del "%PROJECT_ROOT%\%RELEASE_DIR_NAME%.zip"
    echo [INFO] Old release zip removed.
)
echo.

REM --- Step 3: Scaffolding ---
echo [INFO] Creating new release directory structure...
mkdir "%RELEASE_DIR%"
mkdir "%RELEASE_DIR%\packages"
mkdir "%RELEASE_DIR%\python-embed"
mkdir "%RELEASE_DIR%\%PROJECT_NAME%"
if %errorlevel% neq 0 (
    echo [ERROR] Failed to create directory structure. Aborting.
    pause
    exit /b 1
)
echo [INFO] Directory structure created.
echo.

REM --- Step 4: Automated Python Extraction ---
echo [INFO] Extracting Python embeddable package...
tar -xf "%SCRIPT_DIR%python-3.12.10-embed-amd64.zip" -C "%RELEASE_DIR%\python-embed"
if not exist "%RELEASE_DIR%\python-embed\python.exe" (
    echo [ERROR] python.exe not found after extraction! Check if tar command is available and the zip file is correct. Aborting.
    pause
    exit /b 1
)
echo [INFO] Embedded Python extracted successfully.
echo.

REM --- Step 5: Copy All Necessary Source Code & Data ---
echo [INFO] Copying all application source code into subfolder...

REM Use robocopy for robust, recursive copying. Exclude temporary/unnecessary dirs and data index.
robocopy "%PROJECT_ROOT%" "%RELEASE_DIR%\%PROJECT_NAME%" /e /xd __pycache__ .git .vscode .idea .pytest_cache build_release_scripts game_data_index
if %errorlevel% gtr 7 (
    echo [ERROR] Robocopy failed to copy source code. Aborting.
    pause
    exit /b 1
)

echo [INFO] Copying game data index to release root...
robocopy "%PROJECT_ROOT%\game_data_index" "%RELEASE_DIR%\game_data_index" /e
if %errorlevel% gtr 7 (
    echo [ERROR] Robocopy failed to copy game data index. Aborting.
    pause
    exit /b 1
)

REM Ensure the final requirements file is named correctly for the setup script.
copy "%PROJECT_ROOT%\requirements-offline.txt" "%RELEASE_DIR%\requirements.txt" /y

echo [INFO] Source code and data copied.
echo.

REM --- Step 5.6: Copy Pre-written Setup & Run Scripts ---
echo [INFO] Copying portable setup.bat and run.bat...
copy "%SCRIPT_DIR%setup.bat" "%RELEASE_DIR%\setup.bat" /y
copy "%SCRIPT_DIR%run.bat" "%RELEASE_DIR%\run.bat" /y
copy "%SCRIPT_DIR%get-pip.py" "%RELEASE_DIR%\python-embed\get-pip.py" /y
if %errorlevel% neq 0 (
    echo [ERROR] Failed to copy setup/run scripts.
    pause
    exit /b 1
)
echo [INFO] Portable scripts copied successfully.
echo.

REM --- Step 6: Vendor Dependencies ---
echo [INFO] Downloading all dependencies to 'packages' folder...
pushd "%RELEASE_DIR%"
python -m pip download -v -r "%RELEASE_DIR%\requirements.txt" -d "packages" > "pip_log.txt" 2>&1
set "PIP_DOWNLOAD_RESULT=%errorlevel%"
popd
if %PIP_DOWNLOAD_RESULT% neq 0 (
    echo [ERROR] 'pip download' failed. Please check 'pip_log.txt' in the release directory for details. Aborting.
    pause
    exit /b 1
)
echo [INFO] All dependencies downloaded successfully.
echo.

REM --- Step 7: Final Packaging ---
echo [INFO] Attempting to create ZIP archive...
set "SEVENZIP_PATH="
if exist "%ProgramFiles%\7-Zip\7z.exe" set "SEVENZIP_PATH=%ProgramFiles%\7-Zip\7z.exe"
if exist "%ProgramFiles(x86)%\7-Zip\7z.exe" set "SEVENZIP_PATH=%ProgramFiles(x86)%\7-Zip\7z.exe"

if not "%SEVENZIP_PATH%"=="" (
    echo [INFO] 7-Zip found. Compressing...
    "%SEVENZIP_PATH%" a -tzip "%PROJECT_ROOT%\%RELEASE_DIR_NAME%.zip" "%RELEASE_DIR%"
    echo [INFO] ZIP archive created: %PROJECT_ROOT%\%RELEASE_DIR_NAME%.zip
) else (
    echo [WARNING] 7-Zip not found. Skipping automatic zipping.
    echo [ACTION REQUIRED] Please manually zip the folder: %RELEASE_DIR%
}
echo.

REM --- Build Complete ---
echo =================================================================
echo [SUCCESS] Build process completed!
echo The release package is in: %RELEASE_DIR%
echo =================================================================
pause
