# Article Agent V1

一个面向后端开发者的 AI Agent 第一版原型：

- 抓取文章网页
- 提取正文
- 切分 chunk
- 生成 embeddings
- 写入本地 Chroma
- 额外生成可供人工审阅的 Markdown 知识卡片

## 项目结构

```text
app/
  api/
    routes.py
  models/
    schemas.py
  services/
    chunker.py
    crawler.py
    embedder.py
    extractor.py
    markdown_store.py
    summarizer.py
    vector_store.py
  config.py
  main.py
data/
  chroma/
knowledge_base/
  articles/
```

## 环境变量

在项目根目录创建 `.env`：

```env
OPENAI_API_KEY=your_api_key
OPENAI_EMBEDDING_MODEL=text-embedding-3-small
OPENAI_CHAT_MODEL=gpt-4.1-mini
CHROMA_PATH=./data/chroma
KNOWLEDGE_BASE_PATH=./knowledge_base/articles
REQUEST_TIMEOUT_SECONDS=20
CHUNK_SIZE=1000
CHUNK_OVERLAP=150
TOP_K_DEFAULT=5
```

## 安装依赖

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e .
```

## 启动服务

```bash
uvicorn app.main:app --reload
```

启动后访问：

- `GET /` 前端页面
- `GET /health`
- `POST /ingest`
- `POST /search`

## 示例请求

### 写入文章

```bash
curl -X POST http://127.0.0.1:8000/ingest \
  -H "Content-Type: application/json" \
  -d '{"url":"https://example.com/article"}'
```

### 检索内容

```bash
curl -X POST http://127.0.0.1:8000/search \
  -H "Content-Type: application/json" \
  -d '{"query":"这篇文章主要在讲什么？","top_k":3}'
```

## 第一版说明

这是一个适合学习和原型验证的版本：

- 向量数据库使用本地 `Chroma`
- 人类可读归档使用 `knowledge_base/articles/*.md`
- 一篇文章入库时会同时写向量库和 Markdown 卡片

更完整的方案说明见：

- [agent-v1-plan.md](/Users/supernoodle/Documents/Codex/2026-04-21-codex-ai-agent/agent-v1-plan.md)
- [human-readable-knowledge-base.md](/Users/supernoodle/Documents/Codex/2026-04-21-codex-ai-agent/human-readable-knowledge-base.md)
