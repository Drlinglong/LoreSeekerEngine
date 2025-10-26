@echo off
echo Starting LightRAG Server...
echo Make sure you have set the required API key environment variables.
echo.

python -m lightrag.api.lightrag_server --working-dir ./game_data_index --llm-binding openai --embedding-binding openai

pause
