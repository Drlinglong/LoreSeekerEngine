import os
import json
import glob
import asyncio
import httpx
import re
import itertools
from openai import AsyncOpenAI
from lightrag.lightrag import LightRAG
from lightrag.utils import EmbeddingFunc
from preprocessor import get_processed_docs
from lightrag.kg.shared_storage import initialize_pipeline_status
import json_repair

# --- Configuration ---
# API keys are expected to be set as environment variables
SILICONFLOW_API_KEY = os.environ.get("SILICONFLOW_API_KEY") # Used for reranking, embeddings, and now KG extraction

# Directory where the precomputed data will be stored
WORKING_DIR = "./game_data_index"
# Directory containing the source data
DATA_SOURCE_DIR = "data/Wuthering Waves/*.jsonl"

# --- Model & RAG Initialization ---



# 2. Embedding function using SiliconFlow API
def get_embedding_func():
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
    if not SILICONFLOW_API_KEY:
        raise ValueError("SILICONFLOW_API_KEY environment variable is not set for reranking.")

    async def rerank_func(query: str, documents: list[dict], top_n: int = None) -> list[dict]:
        if not documents:
            return []

        doc_texts = [doc.get('text', '') for doc in documents]

        try:
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


async def no_op_llm_func(*args, **kwargs):
    """A dummy LLM function that does nothing and returns an empty string."""
    return ""

async def initialize_rag():
    """Initializes the LightRAG instance for a vector-only setup."""

    embedder = get_embedding_func()
    reranker = await get_siliconflow_reranker_func()

    rag = LightRAG(
        working_dir=WORKING_DIR,
        llm_model_func=no_op_llm_func,  # Use the no-op function to disable KG
        embedding_func=embedder,
        rerank_model_func=reranker,
        llm_model_max_async=128,
        embedding_func_max_async=128,
        max_parallel_insert=128,
        max_graph_nodes=16  # This parameter is now effectively ignored
    )
    await rag.initialize_storages()
    await initialize_pipeline_status()
    return rag

# --- Data Processing ---
async def process_data(rag: LightRAG):
    """
    Finds all .jsonl files, processes them using the external preprocessor,
    and inserts the resulting logical documents into LightRAG in batches.
    """
    jsonl_files = glob.glob(DATA_SOURCE_DIR)
    if not jsonl_files:
        print(f"No .jsonl files found in {DATA_SOURCE_DIR}")
        return

    print(f"Found {len(jsonl_files)} files to process with dynamic strategies.")
    BATCH_SIZE = 50  # Process 50 LOGICAL documents at a time

    doc_batch = []
    id_batch = []
    path_batch = []

    for file_path in jsonl_files:
        print(f"Processing file with dispatcher: {file_path}")
        for doc in get_processed_docs(file_path):
            doc_batch.append(doc['text'])
            id_batch.append(doc['doc_id'])
            # Use the source file from the doc's metadata
            path_batch.append(doc['metadata']['source_file'])

            if len(doc_batch) >= BATCH_SIZE:
                print(f"  - Processing batch of {len(doc_batch)} logical documents...")
                await rag.ainsert(input=doc_batch, ids=id_batch, file_paths=path_batch)
                print(f"  - Batch inserted.")
                doc_batch, id_batch, path_batch = [], [], []

    # Process the final batch
    if doc_batch:
        print(f"  - Processing final batch of {len(doc_batch)} logical documents...")
        await rag.ainsert(input=doc_batch, ids=id_batch, file_paths=path_batch)
        print(f"  - Final batch inserted.")

    print("Data processing complete.")
# --- Main Execution ---
async def main():
    rag_instance = None
    try:
        print("Starting DEV data preprocessing (using SiliconFlow Reranker)...")
        if not SILICONFLOW_API_KEY: # This is the change
            print("Error: SILICONFLOW_API_KEY environment variable is not set.")
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
