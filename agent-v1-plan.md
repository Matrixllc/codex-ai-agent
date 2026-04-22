# AI Agent 第一版方案记录

## 目标

实现一个最小可用的文章入库 Agent 第一版，完成以下能力：

1. 接收一个文章 URL
2. 抓取网页 HTML
3. 提取文章正文
4. 清洗文本内容
5. 按 chunk 切分
6. 生成 embedding
7. 写入本地向量数据库
8. 支持后续相似度检索

这个版本优先追求：

- 简单
- 可运行
- 可理解
- 方便后续迭代到正式工程架构

## 第一版技术选型

### 为什么不用第三方云向量数据库

第一版不接 Pinecone、Qdrant Cloud 这类托管服务，原因是：

- 初学阶段不需要先引入云端运维和计费复杂度
- 先把抓取、清洗、切分、embedding、入库这条链路跑通更重要
- 本地调试更快，更适合验证数据结构和接口设计

### 为什么不用自己手写一个“虚拟向量库”

第一版也不建议自己手写一个假的向量数据库，原因是：

- 学不到真实向量库的存储和检索方式
- 后面迁移时需要重写
- 容易把时间浪费在造轮子上

### 第一版选择

第一版采用：

- Web 服务：`FastAPI`
- 网页抓取：`httpx`
- 正文提取：`trafilatura`
- 文本切分：自定义 chunk 逻辑
- Embedding：OpenAI Embeddings API
- 向量数据库：`Chroma`
- 持久化方式：`PersistentClient`

## 为什么第一版选 Chroma

选择 Chroma 的原因：

- 本地启动快，适合快速验证
- 支持持久化到本地目录
- Python 接入简单
- 对“文章切块后入库”的场景足够直接
- 后续迁移到 Qdrant 或 pgvector 时，概念映射比较清晰

第一版的核心目标不是追求最高性能，而是：

- 跑通 ingestion pipeline
- 明确数据模型
- 验证检索效果

## Chroma 在第一版里怎么用

### 运行方式

第一版直接使用 Chroma 的本地持久化模式。

示意：

```python
import chromadb

client = chromadb.PersistentClient(path="./data/chroma")
collection = client.get_or_create_collection(name="articles")
```

这意味着：

- 数据存储在本地磁盘目录
- 不依赖外部云服务
- 服务重启后数据仍然存在

### collection 设计

第一版只需要一个 collection：

- `articles`

collection 中每一条记录不是“一整篇文章”，而是“文章的一个 chunk”。

原因：

- 一整篇文章通常太长，不适合直接做 embedding
- 检索时返回 chunk 比返回整篇更精确
- 后续做 RAG 时更容易拼接上下文

## 数据模型设计

### 一篇文章的处理结果

一篇文章抓取完成后，会被拆成：

- 一条 article 元信息
- 多条 chunk 向量记录

第一版为了简单，可以先把主要数据都放在 Chroma 的 metadata 中，不额外引入关系型数据库。

### Chroma 每条记录建议存储字段

每个 chunk 存这些信息：

- `id`
- `document`
- `embedding`
- `metadata`

其中：

- `id`：全局唯一，例如 `article_<hash>_chunk_<index>`
- `document`：当前 chunk 的正文文本
- `embedding`：当前 chunk 的向量
- `metadata`：该 chunk 的附加信息

### metadata 建议字段

```json
{
  "article_id": "a1b2c3",
  "chunk_index": 0,
  "title": "文章标题",
  "url": "https://example.com/post",
  "source": "example.com",
  "published_at": "2026-04-21T10:00:00",
  "content_length": 836,
  "ingested_at": "2026-04-21T12:30:00"
}
```

### 为什么这样设计

- `article_id` 用来把多个 chunk 归属到同一篇文章
- `chunk_index` 用来恢复原始顺序
- `title` 和 `url` 用来检索结果展示
- `source` 方便按站点过滤
- `published_at` 和 `ingested_at` 方便后续做时间筛选和增量更新

## 数据流设计

第一版的处理流程如下：

```text
POST /ingest
   ->
下载网页
   ->
提取正文
   ->
清洗文本
   ->
切分 chunk
   ->
生成 embeddings
   ->
写入 Chroma
   ->
返回 article_id 和 chunk 数量
```

### 1. 下载网页

输入：

- URL

输出：

- 原始 HTML

建议处理：

- 超时控制
- 基础重试
- User-Agent 设置

### 2. 提取正文

输入：

- HTML

输出：

- 标题
- 正文文本
- 发布时间（如果可提取）

第一版建议优先依赖 `trafilatura`，因为它对文章类页面提取效果通常比较稳定。

### 3. 清洗文本

处理内容：

- 去多余空白
- 去重复换行
- 去无意义短段落
- 标准化文本格式

目标：

- 尽量让 embedding 输入更干净

### 4. 切分 chunk

第一版采用简单规则：

- chunk 大小：`1000` 字符左右
- overlap：`150` 字符左右

这样做的好处：

- 实现简单
- 召回效果通常够用
- 后续可以平滑升级到按语义或标题切分

### 5. 生成 embedding

对每个 chunk 调 embedding 接口。

结果：

- 一个 chunk 对应一个向量

### 6. 写入向量库

将每个 chunk 写入 Chroma：

- `ids`
- `documents`
- `embeddings`
- `metadatas`

### 7. 返回结果

接口返回内容建议包含：

```json
{
  "article_id": "a1b2c3",
  "url": "https://example.com/post",
  "title": "文章标题",
  "chunk_count": 12,
  "status": "success"
}
```

## 为什么这已经算第一版 Agent

严格来说，这一版更接近“智能数据处理流水线”，不是高度自治的 autonomous agent。

但它已经具备 agent 系统常见的基础模块：

- 输入任务
- 调用工具
- 处理外部数据
- 产生结构化结果
- 写入可供后续检索的记忆层

如果后续继续扩展：

- 自动发现新 URL
- 自动筛选高质量文章
- 自动去重
- 自动重试失败任务
- 自动打标签

那么这个系统就会逐步演化成更完整的 agent。

## 第一版接口建议

### 1. 入库接口

`POST /ingest`

请求：

```json
{
  "url": "https://example.com/post"
}
```

返回：

```json
{
  "article_id": "a1b2c3",
  "title": "文章标题",
  "chunk_count": 12,
  "status": "success"
}
```

### 2. 检索接口

`POST /search`

请求：

```json
{
  "query": "这篇文章主要讲了什么",
  "top_k": 5
}
```

返回：

```json
{
  "results": [
    {
      "score": 0.91,
      "text": "匹配到的 chunk 内容",
      "title": "文章标题",
      "url": "https://example.com/post",
      "chunk_index": 2
    }
  ]
}
```

## 第一版目录建议

```text
app/
  main.py
  api/
    routes.py
  services/
    crawler.py
    extractor.py
    chunker.py
    embedder.py
    vector_store.py
  models/
    schemas.py
data/
  chroma/
```

## 第一版不做什么

为了控制复杂度，第一版先不做：

- 批量 URL 调度
- 定时抓取
- 站点发现
- 去重索引优化
- 多租户
- 权限隔离
- rerank
- 混合检索
- 独立 metadata 数据库
- 异步任务队列

这些都适合第二版再加。

## 第一版的优点

- 学习曲线平缓
- 很快能跑起来
- 本地开发和调试体验好
- 足够支撑后续 RAG 检索实验
- 方便逐步演进到更正式的架构

## 第一版的局限

- Chroma 更适合本地原型，不是最终生产形态
- metadata 和向量数据耦合较紧
- 大规模数据下不如专业向量服务灵活
- 文章抓取质量会受网页结构影响

## 第二版演进方向

后续可以按这个顺序升级：

1. 增加 URL 去重和内容去重
2. 增加批量 ingestion
3. 将 metadata 拆到 Postgres
4. 将向量库切换到 `pgvector` 或 `Qdrant`
5. 增加任务队列和异步处理
6. 增加自动发现和自动分类能力

## 当前结论

第一版推荐方案是：

- 不用第三方托管向量数据库
- 不自己造虚拟向量库
- 使用本地 `Chroma PersistentClient`
- 先把“抓文章 -> 提取正文 -> chunk -> embedding -> 入库 -> 检索”整条链路跑通

这是最适合当前学习阶段、同时也最贴近后端工程实践的起点。
