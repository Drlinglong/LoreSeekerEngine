import os
import json
import glob
import asyncio
import httpx
import re
from openai import AsyncOpenAI
from lightrag.lightrag import LightRAG
from lightrag.utils import EmbeddingFunc
from lightrag.kg.shared_storage import initialize_pipeline_status
import json_repair

# --- Configuration ---
# API keys are expected to be set as environment variables for development
XAI_API_KEY = os.environ.get("XAI_API_KEY")
JINA_API_KEY = os.environ.get("JINA_API_KEY") # For developer's reranker
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY") # For embeddings

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
        timeout=httpx.Timeout(3600.0),
    )

    async def llm_model_func(prompt: str, system_prompt: str = None, history_messages: list = None, hashing_kv=None, **kwargs) -> str:
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

# 2. Embedding function using SiliconFlow API
def get_embedding_func():
    SILICONFLOW_API_KEY = os.environ.get("SILICONFLOW_API_KEY")
    if not SILICONFLOW_API_KEY:
        raise ValueError("SILICONFLOW_API_KEY environment variable is not set for embeddings.")

    sf_client = AsyncOpenAI(
        api_key=SILICONFLOW_API_KEY,
        base_url="https://api.siliconflow.cn/v1"
    )

    async def sf_embed_func(texts: list[str]) -> list[list[float]]:
        response = await sf_client.embeddings.create(
            model="BAAI/bge-m3",
            input=texts
        )
        return [embedding.embedding for embedding in response.data]

    return EmbeddingFunc(embedding_dim=1024, func=sf_embed_func)

# 3. Reranker function using SiliconFlow's API
async def get_siliconflow_reranker_func():
    SILICONFLOW_API_KEY = os.environ.get("SILICONFLOW_API_KEY")
    if not SILICONFLOW_API_KEY:
        raise ValueError("SILICONFLOW_API_KEY environment variable is not set for reranking.")

    sf_client = AsyncOpenAI(
        api_key=SILICONFLOW_API_KEY,
        base_url="https://api.siliconflow.cn/v1"
    )

    async def rerank_func(query: str, documents: list[dict], top_n: int = None) -> list[dict]:
        if not documents:
            return []

        doc_texts = [doc['text'] for doc in documents]

        try:
            # SiliconFlow's rerank is not a standard OpenAI endpoint, so we call it with httpx
            # However, the python SDK might support it. Let's assume it's a custom call for now.
            # The provided documentation shows a /rerank endpoint.
            # The openai-python library does not have a client.rerank method.
            # We will use httpx like in the old jina function.
            rerank_url = "https://api.siliconflow.cn/v1/rerank"
            headers = {
                "accept": "application/json",
                "content-type": "application/json",
                "authorization": f"Bearer {SILICONFLOW_API_KEY}"
            }
            payload = {
                "model": "BAAI/bge-reranker-v2-m3",
                "query": query,
                "documents": doc_texts,
                "top_n": top_n or len(doc_texts),
                "return_documents": False
            }
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(rerank_url, headers=headers, json=payload)
                response.raise_for_status()
                results = response.json().get("results", [])

                reranked_docs = []
                for result in results:
                    original_doc = documents[result['index']]
                    # Add metadata if it doesn't exist
                    if 'metadata' not in original_doc:
                        original_doc['metadata'] = {}
                    original_doc['metadata']['rerank_score'] = result['relevance_score']
                    reranked_docs.append(original_doc)
                
                return reranked_docs

        except httpx.HTTPStatusError as e:
            print(f"Error during reranking with SiliconFlow API: {e}")
            print(f"Response body: {e.response.text}")
            return documents[:top_n] if top_n else documents
        except Exception as e:
            print(f"An unexpected error occurred during reranking with SiliconFlow API: {e}")
            return documents[:top_n] if top_n else documents
            
    return rerank_func

async def initialize_rag():
    """Initializes the LightRAG instance with the correct models for development."""

    llm_func = await get_xai_llm_func()
    embedder = get_embedding_func()
    reranker = await get_siliconflow_reranker_func()

    rag = LightRAG(
        working_dir=WORKING_DIR,
        llm_model_func=llm_func,
        embedding_func=embedder,
        rerank_model_func=reranker,
        llm_model_max_async=16,
        embedding_func_max_async=16,
        max_parallel_insert=16
    )
    await rag.initialize_storages()
    await initialize_pipeline_status()
    return rag

# --- Data Processing ---
async def process_data(rag: LightRAG):
    """Finds, reads, and processes all .jsonl files in batches."""
    jsonl_files = glob.glob(DATA_SOURCE_DIR)
    if not jsonl_files:
        print(f"No .jsonl files found in {DATA_SOURCE_DIR}")
        return

    print(f"Found {len(jsonl_files)} files to process.")
    BATCH_SIZE = 100  # Process 100 documents at a time

    for file_path in jsonl_files:
        print(f"Processing file: {file_path}")
        doc_batch = []
        id_batch = []
        path_batch = []
        line_num = 0

        with open(file_path, 'r', encoding='utf-8') as f:
            for i, line in enumerate(f):
                line_num = i + 1
                try:
                    data = json.loads(line)
                    doc_id = data.get("doc_id")
                    text = data.get("text")

                    if not doc_id or not text:
                        print(f"Skipping line {line_num} in {file_path} due to missing 'doc_id' or 'text'.")
                        continue
                    
                    # Replace {PlayerName} and its variants with "漂泊者"
                    text = re.sub(r'\{PlayerName\}\{Male=.*?Female=.*?\}|\{PlayerName\}', '漂泊者', text)
                    
                    doc_batch.append(text)
                    id_batch.append(doc_id)
                    path_batch.append(file_path)

                    if len(doc_batch) >= BATCH_SIZE:
                        print(f"  - Processing batch of {len(doc_batch)} documents (up to line {line_num})...")
                        await rag.ainsert(input=doc_batch, ids=id_batch, file_paths=path_batch)
                        print(f"  - Batch inserted.")
                        doc_batch, id_batch, path_batch = [], [], []

                except json.JSONDecodeError:
                    print(f"Skipping line {line_num} in {file_path} due to invalid JSON.")
                except Exception as e:
                    print(f"An error occurred while processing batch around line {line_num}: {e}")
                    # Clear batch to avoid reprocessing failed data
                    doc_batch, id_batch, path_batch = [], [], []
        
        # Process the final batch if any documents are left
        if doc_batch:
            print(f"  - Processing final batch of {len(doc_batch)} documents (up to line {line_num})...")
            try:
                await rag.ainsert(input=doc_batch, ids=id_batch, file_paths=path_batch)
                print(f"  - Final batch inserted.")
            except Exception as e:
                print(f"An error occurred while processing the final batch: {e}")


    print("Data processing complete.")

# --- Main Execution ---
async def main():
    rag_instance = None
    try:
        print("Starting DEV data preprocessing (using SiliconFlow Reranker)...")
        if not all([XAI_API_KEY, os.environ.get("SILICONFLOW_API_KEY")]):
            print("Error: One or more required API keys (XAI_API_KEY, SILICONFLOW_API_KEY) are not set.")
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
