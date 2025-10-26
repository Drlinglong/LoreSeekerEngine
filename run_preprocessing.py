import os
import json
import glob
import asyncio
from lightrag.lightrag import LightRAG
from lightrag.components.model_client import Groq, OpenAIEmbeddings, JinaRerank
from lightrag.core.types import Document

# --- Configuration ---
# API keys are expected to be set as environment variables
# For example: export GROQ_API_KEY='your_grok_api_key'
GROQ_API_KEY = os.environ.get("GROQ_API_KEY")
JINA_API_KEY = os.environ.get("JINA_API_KEY")
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY") # Used for embeddings

# Directory where the precomputed data will be stored
WORKING_DIR = "./game_data_index"
# Directory containing the source data
DATA_SOURCE_DIR = "data/Wuthering Waves/*.jsonl"

# --- Model & RAG Initialization ---
def initialize_rag():
    """Initializes the LightRAG instance with models and storage."""
    if not all([GROQ_API_KEY, JINA_API_KEY, OPENAI_API_KEY]):
        print("Error: One or more API keys are not set.")
        print("Please set GROQ_API_KEY, JINA_API_KEY, and OPENAI_API_KEY environment variables.")
        exit(1)

    # Initialize models
    llm = Groq(api_key=GROQ_API_KEY, model="gemma-7b-it") # Using a different model as grok-4-fast is not available
    embedder = OpenAIEmbeddings(api_key=OPENAI_API_KEY, model="text-embedding-3-large")
    reranker = JinaRerank(api_key=JINA_API_KEY)

    # Initialize LightRAG with the specified working directory
    rag = LightRAG(
        working_dir=WORKING_DIR,
        llm=llm,
        embedder=embedder,
        reranker=reranker
    )
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

                    # Create a Document object and insert it into the RAG system
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
    print("Starting data preprocessing...")
    rag_instance = initialize_rag()
    await process_data(rag_instance)
    print("Preprocessing finished.")

if __name__ == "__main__":
    asyncio.run(main())
