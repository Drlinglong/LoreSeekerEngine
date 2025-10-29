@echo off
pushd "%~dp0"
chcp 65001 >nul
title Project Remis - Portable Setup

echo =================================================================
echo.
echo                  Project Remis - Portable Setup
echo.
echo This script will set up the required Python packages.
echo It only needs to be run once.
echo.
echo =================================================================
echo.

REM --- Step 1: Set up the portable Python environment ---
echo [INFO] Activating portable Python environment...
set "PATH=%CD%\python-embed;%CD%\python-embed\Scripts;%PATH%"
echo [INFO] Environment ready.
echo.

REM --- Step 2: The Silver Bullet - UNCOMMENT 'import site' in ._pth file ---
echo [INFO] Applying the 'import site' fix to the ._pth file...
set "PTH_FILE=%CD%\python-embed\python312._pth"
if exist "%PTH_FILE%" (
    echo [INFO] Found path configuration file: python310._pth
    (
        echo python310.zip
        echo .
        echo import site
    ) > "%PTH_FILE%"
    set "PTH_FIX_APPLIED=1"
    echo [INFO] Path configuration file has been patched.
)
if not "%PTH_FIX_APPLIED%"=="1" (
    echo [WARNING] python310._pth file not found or could not be patched.
)
echo.

REM --- Step 3: Pip Bootstrapping ---
echo [INFO] Verifying pip installation...
python -m pip --version >nul 2>nul
if not errorlevel 1 goto :pip_is_ok

echo [WARNING] pip not found or failed. Installing it from local package...
REM The build script should have placed get-pip.py here
if not exist "%CD%\python-embed\get-pip.py" (
    echo [ERROR] get-pip.py not found! The release package is incomplete.
    pause
    popd
    exit /b 1
)
pushd "%CD%\python-embed"
python.exe get-pip.py
popd

:pip_is_ok
echo [INFO] pip is available.
echo.

REM --- Step 4: Install dependencies from the internet using a domestic mirror ---
echo [INFO] Installing dependencies from requirements.txt using a fast mirror...
python -m pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
if not errorlevel 1 (
    echo [SUCCESS] All dependencies installed successfully.
) else (
    echo [ERROR] Failed to install dependencies. Please check your internet connection and try again.
    goto :final_error
)
echo.

REM --- Step 5: Create the .env file for the API key ---
echo [INFO] Creating .env file for your API key...
if exist ".env" (
    echo [INFO] .env file already exists.
) else (
    echo # Please rename this file to .env and fill in your API key. > .env.example
    echo SILICONFLOW_API_KEY="YOUR_API_KEY_HERE" >> .env.example
    echo [INFO] .env.example file created. Please rename it to .env and edit it with your API key.
)
echo.

echo =================================================================
echo [SUCCESS] Setup complete!
echo You can now use run.bat to start the application.
echo =================================================================
echo.
popd
pause