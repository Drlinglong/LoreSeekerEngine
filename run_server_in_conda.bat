@echo off
rem This script is for developers to run the server in a specific Conda environment.

rem 1. Configuration
set CONDA_ROOT=K:\MiniConda
set ENV_NAME=Loreseek

echo ========================================
echo Starting LightRAG Server via Conda for DEV...
echo ----------------------------------------

rem 2. Check Conda Root Path
if not exist "%CONDA_ROOT%\condabin\conda.bat" (
    echo CRITICAL ERROR: Conda installation not found at "%CONDA_ROOT%".
    echo Please check CONDA_ROOT path in this script or install Miniconda.
    goto :final_error
)

rem 3. Activation
echo Status: Conda found. Activating environment '%ENV_NAME%'...
call "%CONDA_ROOT%\condabin\conda.bat" activate %ENV_NAME%
if errorlevel 1 (
    echo CRITICAL ERROR: Failed to activate Conda environment '%ENV_NAME%'.
    goto :final_error
)

echo Environment activated.

rem 4. Install Dependencies
echo Checking and installing dependencies...
rem Use py -m pip for robustness, in case pip is not directly in the activated env's path
python -m pip install -r requirements-offline.txt
if errorlevel 1 (
    echo CRITICAL ERROR: Failed to install dependencies.
    goto :final_error
)

rem 5. Set Environment Variables for this session
echo Setting model configurations via environment variables...

rem --- LLM Configuration (for query generation) ---
set LLM_BINDING=openai
set LLM_BINDING_HOST=https://api.siliconflow.cn/v1
set LLM_MODEL=Qwen/Qwen3-VL-30B-A3B-Instruct
set LLM_BINDING_API_KEY=%SILICONFLOW_API_KEY%

rem --- Embedding Configuration (for query vectorization) ---
set EMBEDDING_BINDING=openai
set EMBEDDING_BINDING_HOST=https://api.siliconflow.cn/v1
set EMBEDDING_MODEL=BAAI/bge-m3
set EMBEDDING_BINDING_API_KEY=%SILICONFLOW_API_KEY%

rem --- Reranker Configuration (using 'jina' binding for SiliconFlow) ---
set RERANK_BINDING=jina
set RERANK_BINDING_HOST=https://api.siliconflow.cn/v1/rerank
set RERANK_MODEL=BAAI/bge-reranker-v2-m3
set RERANK_BINDING_API_KEY=%SILICONFLOW_API_KEY%

rem --- RAG Context Configuration ---
set CHUNK_TOP_K=50

rem 6. Run Server
echo Starting LightRAG server...
python -m lightrag.api.lightrag_server --working-dir ./game_data_index

:final_error
echo.
echo Server stopped or failed to start.
pause
