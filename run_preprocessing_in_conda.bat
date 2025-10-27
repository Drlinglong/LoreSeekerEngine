@echo off
rem 1. Configuration
set CONDA_ROOT=K:\MiniConda
set ENV_NAME=Loreseek
set PYTHON_SCRIPT=run_preprocessing.py

echo ========================================
echo Starting LoreSeeker Preprocessor via Conda...
echo ----------------------------------------

rem 2. Check Conda Root Path
if not exist "%CONDA_ROOT%\condabin\conda.bat" (
    echo CRITICAL ERROR: Conda installation not found at "%CONDA_ROOT%".
    echo Please check CONDA_ROOT path in this script or install Miniconda.
    goto :final_error
)

rem === 3. Isolated Activation and Execution ===
echo Status: Conda found. Launching isolated session for environment (%ENV_NAME%)...

rem Use 'call' to ensure the conda environment is activated correctly within the script's context.
call "%CONDA_ROOT%\condabin\conda.bat" activate %ENV_NAME%

if errorlevel 1 (
    echo CRITICAL ERROR: Failed to activate Conda environment '%ENV_NAME%'.
    goto :final_error
)

echo Environment activated. Running Python script...
python %PYTHON_SCRIPT%

echo.
echo Preprocessing finished.

:final_error
pause