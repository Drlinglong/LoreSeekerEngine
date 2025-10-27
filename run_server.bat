@echo off
echo Checking and installing dependencies...
pip install -r requirements-offline.txt
echo.
echo Starting LightRAG Server...
echo Make sure you have set the required API key environment variables (SILICONFLOW_API_KEY).
echo.

python -m lightrag.api.lightrag_server ^
    --working-dir ./game_data_index ^
    --llm-binding openai ^
    --llm-binding-host "https://api.siliconflow.cn/v1" ^
    --llm-model "Qwen/Qwen3-VL-235B-A22B-Instruct" ^
    --llm-binding-api-key "%SILICONFLOW_API_KEY%" ^
    --embedding-binding openai ^
    --embedding-binding-host "https://api.siliconflow.cn/v1" ^
    --embedding-model "BAAI/bge-m3" ^
    --embedding-binding-api-key "%SILICONFLOW_API_KEY%" ^
    --chunk-top-k 50

pause
