@echo off
pushd "%~dp0"
chcp 65001 >nul
title LoreSeekerEngine - Portable Setup

echo =================================================================
echo.
echo                  LoreSeekerEngine - Portable Setup
echo.
echo This script will set up the required Python packages and configure your API key.
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
    echo [INFO] Found path configuration file: python312._pth
    (
        echo python312.zip
        echo .
        echo import site
    ) > "%PTH_FILE%"
    set "PTH_FIX_APPLIED=1"
    echo [INFO] Path configuration file has been patched.
)
if not "%PTH_FIX_APPLIED%"=="1" (
    echo [WARNING] python312._pth file not found or could not be patched.
)
echo.

REM --- Step 3: Pip Bootstrapping ---
echo [INFO] Verifying pip installation...
python -m pip --version >nul 2>nul
if not errorlevel 1 goto :pip_is_ok

echo [WARNING] pip not found or failed. Installing it from local package...
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

REM --- Step 4: Install dependencies from local packages ---
echo [INFO] Installing dependencies from local 'packages' directory...
python -m pip install --no-index --find-links=./packages -r requirements.txt
if not errorlevel 1 (
    echo [SUCCESS] All dependencies installed successfully.
) else (
    echo [ERROR] Failed to install dependencies. Please check the 'packages' folder and requirements.txt.
    goto :final_error
)
echo.

REM --- Step 5: Create the .env file with all configurations ---
echo [INFO] Configuring environment variables...
if exist ".env" (
    echo [INFO] .env file already exists. Skipping creation.
) else (
    echo Please enter your SILICONFLOW_API_KEY and press Enter:
    set /p SILICONFLOW_API_KEY=
    echo [INFO] Creating .env file...
    (
        echo # Environment variables for LoreSeekerEngine
        echo SILICONFLOW_API_KEY=!SILICONFLOW_API_KEY!
        echo LLM_BINDING=openai
        echo LLM_BINDING_HOST=https://api.siliconflow.cn/v1
        echo LLM_MODEL=Qwen/Qwen3-VL-30B-A3B-Instruct
        echo EMBEDDING_BINDING=openai
        echo EMBEDDING_BINDING_HOST=https://api.siliconflow.cn/v1
        echo EMBEDDING_MODEL=BAAI/bge-m3
        echo RERANK_BINDING=jina
        echo RERANK_BINDING_HOST=https://api.siliconflow.cn/v1/rerank
        echo RERANK_MODEL=BAAI/bge-reranker-v2-m3
        echo CHUNK_TOP_K=50
    ) > .env
    echo [INFO] .env file created successfully.
)
echo.

:final_success
echo =================================================================
echo [SUCCESS] Setup complete!
echo You can now use run.bat to start the application.
echo =================================================================
echo.
goto :end

:final_error
echo =================================================================
echo [ERROR] Setup failed. Please review the error messages above.
echo =================================================================
echo.

:end
popd
pause
