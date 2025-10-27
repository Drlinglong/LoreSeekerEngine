# 鸣潮游戏文本检索工具 (LoreSeeker Engine for Wuthering Waves)

## 项目概览

本项目是一个为B站游戏内容创作者（及所有《鸣潮》爱好者）设计的检索增强生成（RAG）工具，旨在帮助用户高效地查找、考据游戏内的文本资料。

它使用 `LightRAG` 框架构建，通过预计算知识图谱和向量索引，提供快速、精准的的游戏知识问答体验。

## 文件结构

- `data/Wuthering Waves/`: 存放处理好的《鸣潮》游戏文本数据 (`.jsonl`格式)。
- `run_preprocessing_dev.py`: **供开发者使用**的预计算脚本 (使用 Jina Reranker)。
- `run_server.bat`: 用于启动后端API服务的Windows批处理脚本。
- `lightrag_webui/`: 前端Web界面源代码。

---

## 如何使用 (最终用户指南)

本工具已包含所有预计算好的数据，开箱即用。

### 步骤 1: 启动服务

直接双击根目录下的 `run_server.bat` 文件。

程序会自动启动一个本地Web服务，请勿关闭弹出的命令行窗口。

### 步骤 2: 开始使用

在浏览器中打开 `http://127.0.0.1:8000` (或命令行窗口中提示的地址)，即可开始与《鸣潮》游戏知识库进行对话。

---

## 开发者说明

本部分面向需要从原始数据文件重新构建知识库的开发者。

### 构建知识库 (预计算)

如果您修改了 `data/Wuthering Waves/` 中的源文件，或者想要调整预处理逻辑，您需要运行预计算脚本来重新生成 `game_data_index` 文件夹。

1.  **设置API密钥**:
    确保以下 API 密钥已设置为您的系统环境变量。脚本会自动读取它们。

    - `XAI_API_KEY`: 用于知识图谱构建 (使用 xAI 的 `grok-4-fast` 模型)。
    - `SILICONFLOW_API_KEY`: 用于文本向量化 (使用 `BAAI/bge-m3`) 和文本重排序 (使用 `BAAI/bge-reranker-v2-m3`)。

2.  **运行预处理脚本**:
    在项目根目录打开命令行，运行以下脚本：
    ```bash
    python run_preprocessing.py
    ```
    这个过程会消耗大量时间和计算资源，因为它会调用外部API进行知识图谱构建和向量化。完成后，新生成的 `game_data_index` 文件夹将包含最新的知识库。
