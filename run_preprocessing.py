import os
import json
import glob
import asyncio
import httpx
import re
from openai import AsyncOpenAI
from lightrag.lightrag import LightRAG
from lightrag.core import Document, Embedder
from lightrag.kg.shared_storage import initialize_pipeline_status

# --- Configuration ---
# API keys are expected to be set as environment variables
XAI_API_KEY = os.environ.get("XAI_API_KEY")
MODELSCOPE_API_KEY = os.environ.get("MODELSCOPE_API_KEY") # Used for reranking
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


# 3. Reranker function using ModelScope's chat completion endpoint
async def get_modelscope_reranker_func():
    if not MODELSCOPE_API_KEY:
        raise ValueError("MODELSCOPE_API_KEY environment variable is not set for reranking.")

    modelscope_client = AsyncOpenAI(
        api_key=MODELSCOPE_API_KEY,
        base_url="https://api-inference.modelscope.cn/v1",
        timeout=httpx.AsyncTimeout(3600.0),
    )

    async def rerank_func(query: str, documents: list[Document], top_n: int = None) -> list[Document]:
        if not documents:
            return []

        doc_texts = [doc.text for doc in documents]
        numbered_documents = "\n".join([f"[{i}] {doc}" for i, doc in enumerate(doc_texts)])

        prompt = f"""You are an expert relevance ranker. Your task is to reorder a list of documents based on their relevance to a given query.

Query: "{query}"

Documents:
{numbered_documents}

Instructions:
1. Read the query and all the documents carefully.
2. Determine which documents are most relevant to the query.
3. Return a JSON object containing a single key "ranking" which is a list of the original indices of the documents, sorted from most relevant to least relevant.
4. Only include documents that are relevant. If a document is completely irrelevant, do not include its index in the list.
5. Your output MUST be a valid JSON object and nothing else.

Example output for a different query:
{{
  "ranking": [3, 1, 0]
}}
"""
        try:
            response = await modelscope_client.chat.completions.create(
                model="qwen-max-latest",
                messages=[
                    {"role": "system", "content": "You are an expert relevance ranker."},
                    {"role": "user", "content": prompt}
                ],
                response_format={"type": "json_object"},
                temperature=0.0
            )
            message_content = response.choices[0].message.content
            if message_content is None:
                raise ValueError("API returned an empty message.")

            cleaned_json = json_repair.repair_json(message_content)
            sorted_indices = json.loads(cleaned_json).get("ranking", [])

            # Create a map of original index to document
            doc_map = {i: doc for i, doc in enumerate(documents)}

            # Build the reranked list
            reranked_docs = [doc_map[i] for i in sorted_indices if i in doc_map]

            # Add remaining documents that were not ranked to the end
            ranked_indices_set = set(sorted_indices)
            unranked_docs = [doc for i, doc in enumerate(documents) if i not in ranked_indices_set]

            final_docs = reranked_docs + unranked_docs

            return final_docs[:top_n] if top_n else final_docs

        except Exception as e:
            print(f"Error during reranking with ModelScope ChatCompletion: {e}")
            return documents[:top_n] if top_n else documents

    return rerank_func


async def initialize_rag():
    """Initializes the LightRAG instance with the correct models."""

    llm_func = await get_xai_llm_func()
    embedder = get_embedding_func()
    reranker = await get_modelscope_reranker_func()

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
        if not all([XAI_API_KEY, MODELSCOPE_API_KEY, OPENAI_API_KEY]):
            print("Error: One or more required API keys (XAI_API_KEY, MODELSCOPE_API_KEY, OPENAI_API_KEY) are not set.")
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
