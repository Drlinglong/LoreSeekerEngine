import os
import json
import glob
import asyncio
import httpx
from openai import AsyncOpenAI
from lightrag.lightrag import LightRAG
from lightrag.core.types import Document, Embedder
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

# 2. Embedding function using OpenAI API
def get_embedding_func():
    if not OPENAI_API_KEY:
        raise ValueError("OPENAI_API_KEY environment variable is not set for embeddings.")

    openai_client = AsyncOpenAI(api_key=OPENAI_API_KEY)

    async def openai_embed_func(texts: list[str]) -> list[list[float]]:
        response = await openai_client.embeddings.create(
            model="text-embedding-3-large",
            input=texts
        )
        return [embedding.embedding for embedding in response.data]

    return Embedder(model="text-embedding-3-large", async_call=openai_embed_func)

# 3. Reranker function using Jina's REST API
async def get_jina_reranker_func():
    if not JINA_API_KEY:
        raise ValueError("JINA_API_KEY environment variable is not set for reranking.")

    jina_api_url = "https://api.jina.ai/v1/rerank"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {JINA_API_KEY}",
    }

    async def rerank_func(query: str, documents: list[Document], top_n: int = None) -> list[Document]:
        if not documents:
            return []

        doc_texts = [doc.text for doc in documents]

        payload = {
            "model": "jina-reranker-v3",
            "query": query,
            "documents": doc_texts,
            "top_n": top_n or len(doc_texts)
        }

        async with httpx.AsyncClient(timeout=30.0) as client:
            try:
                response = await client.post(jina_api_url, headers=headers, json=payload)
                response.raise_for_status()
                results = response.json().get("results", [])

                # Reorder documents based on the reranker's response
                reranked_docs = []
                for result in results:
                    original_doc = documents[result['index']]
                    original_doc.metadata['rerank_score'] = result['relevance_score']
                    reranked_docs.append(original_doc)

                return reranked_docs
            except httpx.HTTPStatusError as e:
                print(f"Error during reranking with Jina API: {e}")
                print(f"Response body: {e.response.text}")
                # Fallback to original order if reranking fails
                return documents[:top_n] if top_n else documents
            except Exception as e:
                print(f"An unexpected error occurred during reranking with Jina API: {e}")
                return documents[:top_n] if top_n else documents

    return rerank_func

async def initialize_rag():
    """Initializes the LightRAG instance with the correct models for development."""

    llm_func = await get_xai_llm_func()
    embedder = get_embedding_func()
    reranker = await get_jina_reranker_func()

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
        print("Starting DEV data preprocessing (using Jina Reranker)...")
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
