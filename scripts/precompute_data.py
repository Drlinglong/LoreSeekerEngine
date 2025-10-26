import os
import logging
from lightrag.lightrag import LightRAG
from lightrag.components.llm import LiteLLM
from lightrag.components.embedding import VoyageAIEmbedding
from lightrag.components.reranker import JinaReranker

# --- Basic Setup ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# --- 1. USER CONFIGURATION ---
# TODO: 在运行脚本前，请将您的 API 密钥设置为环境变量。
# 例如，在 Windows CMD 中: set GROK_API_KEY=your_grok_api_key
# 在 PowerShell 中: $env:GROK_API_KEY="your_grok_api_key"
GROK_API_KEY = os.getenv("GROK_API_KEY")
VOYAGE_API_KEY = os.getenv("VOYAGE_API_KEY")
JINA_API_KEY = os.getenv("JINA_API_KEY")

# TODO: 请将此路径更改为您的游戏数据文件的实际路径。
# 可以是 .txt, .json, .md 等格式。
DATA_PATH = "path/to/your/game_data.json" # <--- 重要：请修改这里

# --- 2. LightRAG CONFIGURATION ---
WORKING_DIR = "./game_data_index"
CHUNK_TOKEN_SIZE = 700  # 根据计划建议 (500-800)
CHUNK_OVERLAP_TOKEN_SIZE = 100  # 根据计划建议

def precompute_knowledge_base():
    """
    初始化 LightRAG 并处理文档，以构建和保存知识库。
    """
    if not all([GROK_API_KEY, VOYAGE_API_KEY, JINA_API_KEY]):
        logging.error("API keys for Grok, VoyageAI, or Jina are not set. Please set them as environment variables.")
        return
    if DATA_PATH == "path/to/your/game_data.json":
        logging.error(f"Please update the DATA_PATH variable in this script to point to your data file.")
        return
    if not os.path.exists(DATA_PATH):
        logging.error(f"Data file not found at: {DATA_PATH}")
        return

    logging.info("Initializing LightRAG with custom models...")

    # 1. 配置用于图谱提取的 LLM (根据计划)
    graph_builder_llm = LiteLLM(
        api_key=GROK_API_KEY,
        model_name="grok-4-fast",  # 使用计划中指定的模型
        base_url="https://api.groq.com/openai/v1"  # Groq 的 OpenAI 兼容端点
    )

    # 2. 配置 Embedding 模型 (根据计划)
    # 注意：您的计划中提到了 text-embedding-3-large 或 bge-m3。
    # 这里我们使用 VoyageAI 作为示例，因为它在离线依赖中有提及。
    embedding_model = VoyageAIEmbedding(
        api_key=VOYAGE_API_KEY,
        model_name="voyage-2"  # 一个常用的 Voyage 模型，您可以根据需要更改
    )

    # 3. 配置 Reranker (根据计划)
    reranker = JinaReranker(api_key=JINA_API_KEY)

    # 4. 使用自定义组件初始化 LightRAG
    rag = LightRAG(
        working_dir=WORKING_DIR,
        llm=graph_builder_llm,
        embedding=embedding_model,
        reranker=reranker,
    )

    logging.info(f"Starting to process and insert data from: {DATA_PATH}")
    logging.info(f"Chunk size: {CHUNK_TOKEN_SIZE}, Overlap: {CHUNK_OVERLAP_TOKEN_SIZE}")

    # 5. 插入文档。这将触发完整的数据处理流水线。
    try:
        rag.insert(
            doc_path=DATA_PATH,
            chunk_token_size=CHUNK_TOKEN_SIZE,
            chunk_overlap_token_size=CHUNK_OVERLAP_TOKEN_SIZE
        )
        logging.info("Successfully pre-computed and saved the knowledge base.")
        logging.info(f"All data is stored in: {os.path.abspath(WORKING_DIR)}")
    except Exception as e:
        logging.error(f"An error occurred during the LightRAG insertion process: {e}", exc_info=True)

if __name__ == "__main__":
    precompute_knowledge_base()
