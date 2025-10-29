@echo off
pushd "%~dp0"
setlocal enabledelayedexpansion
title Project Remis

echo [INFO] =================================================================
echo [INFO] Project Remis - Portable Toolkit Startup
echo [INFO] =================================================================
echo [INFO] Setting up portable environment...
echo.

REM --- Portable Toolkit Environment Setup ---
REM Temporarily "hijack" the current command-line session environment
set "ORIGINAL_PATH=%PATH%"
set "ORIGINAL_PYTHONPATH=%PYTHONPATH%"
set "ORIGINAL_PYTHONHOME=%PYTHONHOME%"

REM Set portable Python as priority
set "PATH=%CD%\python-embed;%PATH%"
set "PYTHONPATH=%CD%\packages;%CD%\python-embed"
REM PYTHONHOME is not needed and can cause path issues in embedded environments.

echo [INFO] Portable Python environment activated
echo [INFO] Python path: %CD%\python-embed
echo [INFO] Packages path: %CD%\packages
echo.

REM --- Change to portable package directory ---
cd /d "%CD%"

REM --- Skip pip installation for embedded Python ---
echo [INFO] Using pre-installed packages (embedded Python mode)
echo [INFO] Dependencies are already included in the portable package
echo.

REM --- Step 3: Launch the server ---
echo [INFO] Starting the LoreSeeker Engine server...
echo [INFO] This window will show server logs. Do not close it.

python -m lightrag.api.lightrag_server ^
    --working-dir ./game_data_index ^
    --llm-binding openai ^
    --llm-binding-host "https://api.siliconflow.cn/v1" ^
    --llm-model "Qwen/Qwen3-VL-235B-A22B-Instruct" ^
    --embedding-binding openai ^
    --embedding-binding-host "https://api.siliconflow.cn/v1" ^
    --embedding-model "BAAI/bge-m3"

REM --- Restore original environment ---
set "PATH=!ORIGINAL_PATH!"
set "PYTHONPATH=!ORIGINAL_PYTHONPATH!"
set "PYTHONHOME=!ORIGINAL_PYTHONHOME!"

echo [INFO] Project Remis has closed. Environment restored.
pause >nul
popd
