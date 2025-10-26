import os
import json
import glob
import asyncio
import httpx
from openai import AsyncOpenAI
from lightrag.lightrag import LightRAG
from lightrag.components.model_client import JinaRerank, OpenAIEmbeddings
from lightrag.core.types import Document
from lightrag.kg.shared_storage import initialize_pipeline_status

# --- Configuration ---
# API keys are expected to be set as environment variables
XAI_API_KEY = os.environ.get("XAI_API_KEY")
JINA_API_KEY = os.environ.get("JINA_API_KEY")
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY") # Used for embeddings

# Directory where the precomputed data will be stored
WORKING_DIR = "./game_data_index"
# Directory containing the source data
DATA_SOURCE_DIR = "data/Wuthering Waves/*.jsonl"

# --- Model & RAG Initialization ---

# 1. LLM function for xAI Grok
async def get_xai_llm_func():
    if not XAI_API_KEY:
        raise ValueError("XAI_API_KEY environment variable is not set.")

    xai_client = AsyncOpenAI(
        api_key=XAI_API_KEY,
        base_url="https://api.x.ai/v1",
        timeout=httpx.AsyncTimeout(3600.0),
    )

    async def llm_model_func(prompt: str, system_prompt: str = None, history_messages: list = None, **kwargs) -> str:
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        if history_messages:
            messages.extend(history_messages)
        messages.append({"role": "user", "content": prompt})

        completion = await xai_client.chat.completions.create(
            model="grok-4-fast",
            messages=messages,
            **kwargs,
        )
        return completion.choices[0].message.content

    return llm_model_func

# 2. Embedding function
def get_embedding_func():
    if not OPENAI_API_KEY:
        raise ValueError("OPENAI_API_KEY environment variable is not set for embeddings.")
    return OpenAIEmbeddings(api_key=OPENAI_API_KEY, model="text-embedding-3-large")

# 3. Reranker function
def get_reranker_func():
    if not JINA_API_KEY:
        raise ValueError("JINA_API_KEY environment variable is not set for reranking.")
    return JinaRerank(api_key=JINA_API_KEY)

async def initialize_rag():
    """Initializes the LightRAG instance with the correct models."""

    llm_func = await get_xai_llm_func()
    embedder = get_embedding_func()
    reranker = get_reranker_func()

    rag = LightRAG(
        working_dir=WORKING_DIR,
        llm_model_func=llm_func,
        embedder=embedder,
        reranker=reranker
    )
    await rag.initialize_storages()
    await initialize_pipeline_status()
    return rag

# --- Data Processing ---
async def process_data(rag: LightRAG):
    """Finds, reads, and processes all .jsonl files."""
    jsonl_files = glob.glob(DATA_SOURCE_DIR)
    if not jsonl_files:
        print(f"No .jsonl files found in {DATA_SOURCE_DIR}")
        return

    print(f"Found {len(jsonl_files)} files to process.")

    for file_path in jsonl_files:
        print(f"Processing file: {file_path}")
        with open(file_path, 'r', encoding='utf-8') as f:
            for i, line in enumerate(f):
                try:
                    data = json.loads(line)
                    doc_id = data.get("doc_id")
                    text = data.get("text")

                    if not doc_id or not text:
                        print(f"Skipping line {i+1} in {file_path} due to missing 'doc_id' or 'text'.")
                        continue

                    document = Document(doc_id=doc_id, text=text)
                    await rag.ainsert(document)
                    print(f"  - Inserted doc_id: {doc_id}")

                except json.JSONDecodeError:
                    print(f"Skipping line {i+1} in {file_path} due to invalid JSON.")
                except Exception as e:
                    print(f"An error occurred while processing doc_id {doc_id}: {e}")

    print("Data processing complete.")

# --- Main Execution ---
async def main():
    rag_instance = None
    try:
        print("Starting data preprocessing...")
        if not all([XAI_API_KEY, JINA_API_KEY, OPENAI_API_KEY]):
            print("Error: One or more required API keys (XAI_API_KEY, JINA_API_KEY, OPENAI_API_KEY) are not set.")
            exit(1)

        rag_instance = await initialize_rag()
        await process_data(rag_instance)
        print("Preprocessing finished successfully.")
    except Exception as e:
        print(f"An error occurred during preprocessing: {e}")
    finally:
        if rag_instance:
            await rag_instance.finalize_storages()
            print("Storage connections finalized.")

if __name__ == "__main__":
    asyncio.run(main())
