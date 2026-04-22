# 人类可读知识库方案

## 目标

在第一版向量入库方案之外，额外建立一套明显、可查阅、适合人工监督的知识记录方式。

核心诉求：

- 人能直接阅读
- 人能快速检查抓取结果是否准确
- 人能看到文章的大体内容，而不是只看到向量
- 后续可以作为审阅、标注、纠错的基础

## 结论

第一版建议同时保留两套存储：

1. 向量数据库
2. Markdown 知识库

它们的分工如下：

- 向量数据库：给程序做相似度检索
- Markdown 知识库：给人做阅读、抽查、监督、复核

## 为什么第一版优先用 Markdown，而不是图数据库

图数据库当然可以做，但第一版不建议优先上。

原因：

- 图数据库更适合记录实体关系，不是最适合“先让人看文章内容”
- 初学阶段会引入额外的建模复杂度
- 人类阅读图数据不如直接阅读 Markdown 直观
- 当前主要目标是建立“可监督的内容留痕”，Markdown 更简单有效

所以第一版优先选择：

- 向量库存 chunk
- Markdown 存文章摘要和人工可读归档

等第二版再考虑图数据库，用来记录：

- 文章与主题关系
- 作者与站点关系
- 技术概念之间的引用关系
- 文章之间的相似或演化关系

## 推荐的第一版双写策略

每抓取一篇文章时，系统同时做两件事：

1. 将 chunk 和 embedding 写入向量库
2. 将文章摘要和原始信息写入 Markdown 文件

这样我们就能同时获得：

- 机器可检索的记忆
- 人类可审阅的知识卡片

## Markdown 知识库长什么样

建议在项目里增加一个目录：

```text
knowledge_base/
  articles/
```

每篇文章对应一个 Markdown 文件。

文件名建议：

```text
knowledge_base/articles/{article_id}.md
```

例如：

```text
knowledge_base/articles/a1b2c3.md
```

## 每篇文章 Markdown 建议结构

建议每篇文章至少记录下面这些内容：

```md
# 文章标题

## 基本信息

- article_id: a1b2c3
- url: https://example.com/post
- source: example.com
- published_at: 2026-04-21T10:00:00
- ingested_at: 2026-04-21T12:30:00

## 大体介绍

这篇文章主要介绍了什么问题、核心观点是什么、适合什么背景的人阅读。

## 摘要

用 3 到 8 句话概括文章内容。

## 关键词

- agent
- rag
- vector database

## 正文摘录

这里保留清洗后的正文前几段，方便人工快速判断抓取得是否正确。

## Chunk 信息

- chunk_count: 12
- chunk_size: 1000
- overlap: 150

## 备注

记录人工审阅结论、问题、修正建议。
```

## 为什么这种结构适合人工监督

因为人工检查时最关心的通常不是向量本身，而是：

- 这篇文章是不是抓对了
- 标题和正文是否匹配
- 内容是否值得保留
- 摘要是否准确
- 这篇文章大概讲什么

Markdown 可以直接回答这些问题，而且：

- Git 里容易 diff
- 改动容易追踪
- 适合代码仓库协作
- 后续还能补人工标注

## 第一版建议写入哪些“人类可读”字段

第一版推荐至少生成这些字段：

- 标题
- 原始 URL
- 来源站点
- 抓取时间
- 文章大体介绍
- 文章摘要
- 关键词
- 清洗后的正文片段
- chunk 数量

其中“文章大体介绍”和“摘要”特别重要。

它们的区别可以这样理解：

- 大体介绍：偏导读，告诉人这篇文章大概是什么、适合谁看
- 摘要：偏内容压缩，概括文章说了什么

## 第一版中的“网页大体介绍”怎么写

建议控制在 2 到 4 句话，重点回答：

- 这篇文章主要讨论什么主题
- 它更偏教程、观点、新闻、文档还是案例
- 对什么人有价值

例如：

```text
这是一篇面向工程实践的教程型文章，主要介绍如何将网页内容切分并写入向量数据库。内容偏入门实现，适合刚开始搭建 RAG 或知识库系统的后端开发者阅读。
```

## 和向量库的关系

建议把 Markdown 文件和向量库记录通过 `article_id` 关联起来。

也就是说：

- Markdown 文件名里有 `article_id`
- 向量库 metadata 里也保存 `article_id`

这样之后：

- 检索命中 chunk 时，可以反查对应 Markdown
- 人工读完 Markdown 后，也可以追踪这篇文章对应哪些 chunk

## 第一版项目结构建议更新

在原来的目录基础上，新增：

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
    markdown_store.py
  models/
    schemas.py
data/
  chroma/
knowledge_base/
  articles/
```

## markdown_store 的职责

建议增加一个 `markdown_store.py`，负责：

1. 根据文章结构化结果生成 Markdown 文本
2. 将 Markdown 写入 `knowledge_base/articles/`
3. 保证文件名可预测、可追踪

## 第一版处理流更新

新的处理流程：

```text
POST /ingest
   ->
下载网页
   ->
提取正文
   ->
生成大体介绍和摘要
   ->
清洗文本
   ->
切分 chunk
   ->
生成 embeddings
   ->
写入 Chroma
   ->
写入 Markdown 知识库
   ->
返回结果
```

## 是否要存到图数据库

第一版建议先不存图数据库。

如果你特别想为后续扩展预留空间，可以先在 Markdown 中加一组轻量关系字段，例如：

- related_topics
- related_articles
- author
- site_category

这样第二版如果要迁移到图数据库，就有初始结构可以映射。

## 如果第二版要接图数据库，适合存什么

图数据库更适合存关系，而不是原文。

例如：

- `Article -> belongs_to -> Topic`
- `Article -> published_by -> Site`
- `Article -> mentions -> Concept`
- `Article -> similar_to -> Article`

所以更合理的路线是：

- 第一版：向量库 + Markdown
- 第二版：在此基础上补图数据库做关系层

## 当前建议

第一版最适合你的方案是：

1. 用 `Chroma` 做本地向量存储
2. 增加 `knowledge_base/articles/*.md` 做人类可读知识归档
3. 每篇文章在入向量库时，同时生成一份 Markdown 卡片
4. 用 `article_id` 把两边关联起来

这样既满足程序检索，也满足人工查阅和监督。
