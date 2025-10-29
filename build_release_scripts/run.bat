@echo off
pushd "%~dp0"
setlocal enabledelayedexpansion
title LoreSeekerEngine

echo [INFO] =================================================================
echo [INFO] LoreSeekerEngine - Portable Toolkit Startup
echo [INFO] =================================================================
echo.

REM --- Step 1: Activate Portable Environment ---
echo [INFO] Setting up portable environment...
set "PATH=%CD%\python-embed;%CD%\python-embed\Scripts;%PATH%"
set "PYTHONPATH=%CD%\packages;%CD%\python-embed"
echo [INFO] Portable Python environment activated.
echo.

REM --- Step 2: Load Environment Variables from .env file ---
echo [INFO] Loading environment variables from .env file...
if not exist ".env" (
    echo [ERROR] .env file not found. Please run setup.bat first.
    goto :final_error
)
rem This section is now disabled to let Python's dotenv handle environment variables directly.
rem for /f "usebackq delims=" %%a in (".env") do (
rem     set "%%a"
rem )
echo [INFO] Environment variables loaded.
echo.

REM --- Step 3: Verify API Key ---
if not defined SILICONFLOW_API_KEY (
    echo [ERROR] SILICONFLOW_API_KEY is not set in the .env file.
    goto :final_error
)

REM --- Step 4: Launch the server ---
echo [INFO] Starting the LoreSeekerEngine server...
echo [INFO] This window will show server logs. Do not close it.

python -m lightrag.api.lightrag_server --working-dir ./game_data_index

:final_error
echo.
echo [INFO] Server stopped or failed to start.
popd
pause
