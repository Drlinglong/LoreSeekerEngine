@echo off
echo Starting LightRAG Server...
echo Make sure you have set the required API key environment variables (e.g., MODELSCOPE_API_KEY).
echo.

python -m lightrag.api.lightrag_server ^
    --working-dir ./game_data_index ^
    --llm-binding openai ^
    --llm-binding-host "https://dashscope.aliyuncs.com/compatible-mode/v1" ^
    --llm-model "qwen-max-latest" ^
    --llm-binding-api-key "%MODELSCOPE_API_KEY%"

pause
