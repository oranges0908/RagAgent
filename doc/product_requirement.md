# AI Research Paper Assistant — 需求文档 v1.0

## 1. 项目概述

AI Research Paper Assistant 是一款基于 RAG（检索增强生成）技术的学术论文智能问答 Web 应用。用户可上传 PDF 格式的研究论文，通过自然语言提问，系统从论文中检索相关段落并借助 LLM 生成有据可查的答案。

**技术栈：**
- 后端：Python（FastAPI）
- 向量数据库：FAISS
- 前端：Flutter（Web）
- LLM：Claude API（claude-sonnet-4-6）
- Embedding：Sentence Transformers 或 OpenAI Embedding API

---

## 2. 功能需求

### 2.1 论文上传（Paper Upload）

| 编号 | 需求描述 | 优先级 |
|------|----------|--------|
| F-01 | 用户可通过 Web 界面上传 PDF 格式论文 | P0 |
| F-02 | 系统解析 PDF 并提取全文文本 | P0 |
| F-03 | 尽力提取论文章节结构（Abstract、Introduction、Method 等） | P1 |
| F-04 | 存储论文元数据（标题、作者、上传时间、文件名） | P0 |
| F-05 | 支持多篇论文管理，用户可查看已上传论文列表 | P1 |
| F-06 | 支持删除已上传论文及其向量数据 | P2 |

### 2.2 文档摄入 Pipeline（Document Ingestion）

| 编号 | 需求描述 | 优先级 |
|------|----------|--------|
| F-07 | 对提取的文本进行分块处理 | P0 |
| F-08 | chunk_size = 500 字符，chunk_overlap = 100 字符 | P0 |
| F-09 | 为每个 chunk 生成向量 Embedding | P0 |
| F-10 | 将 Embedding 及元数据存入 FAISS 向量数据库 | P0 |
| F-11 | 每个 chunk 需保留来源信息（论文名、章节、chunk 序号） | P0 |

**Pipeline 流程：**
```
PDF 上传
  → 文本提取（PyMuPDF / pdfplumber）
  → 章节识别（启发式规则）
  → 文本分块（chunk_size=500, overlap=100）
  → Embedding 生成
  → FAISS 存储（含元数据索引）
```

### 2.3 语义检索（Semantic Retrieval）

| 编号 | 需求描述 | 优先级 |
|------|----------|--------|
| F-12 | 用户提问时，对问题生成 Embedding | P0 |
| F-13 | 在 FAISS 中执行向量相似度搜索，返回 top_k=3 个 chunk | P0 |
| F-14 | 可按论文 ID 过滤检索范围（单篇或全库） | P1 |
| F-15 | 返回每个 chunk 的相似度分数 | P1 |

### 2.4 LLM 问答生成（Answer Generation）

| 编号 | 需求描述 | 优先级 |
|------|----------|--------|
| F-16 | 将检索到的 chunks 拼接为上下文，调用 LLM 生成答案 | P0 |
| F-17 | 使用规定的 Prompt 模板 | P0 |
| F-18 | 输出结构化结果：Answer + Sources 列表 | P0 |
| F-19 | Sources 包含：论文名、章节、原文摘录 | P0 |
| F-20 | 支持流式输出（Streaming）提升响应体验 | P2 |

**Prompt 模板：**
```
Use the following context to answer the question.

Context:
{retrieved_chunks}

Question:
{user_question}

Answer clearly and cite the source text.
```

**输出示例：**
```
Answer:
The main contribution of the paper is introducing the transformer architecture.

Sources:
- Paper: Attention Is All You Need
  Section: Method
  Quote: "We propose a new simple network architecture, the Transformer..."
```

### 2.5 前端界面（Flutter Web）

| 编号 | 需求描述 | 优先级 |
|------|----------|--------|
| F-21 | 论文上传页：拖拽或点击上传 PDF，显示上传进度 | P0 |
| F-22 | 论文列表页：展示已上传论文，支持选择/删除 | P1 |
| F-23 | 问答页：文本输入框 + 提交按钮，展示 Answer 和 Sources | P0 |
| F-24 | 支持选择针对哪篇论文提问（或全库） | P1 |
| F-25 | Sources 高亮展示，可折叠/展开 | P2 |

---

## 3. 非功能需求

| 编号 | 需求描述 | 指标 |
|------|----------|------|
| NF-01 | API 响应延迟（不含 LLM） | < 500ms |
| NF-02 | 单次问答端到端延迟 | < 10s |
| NF-03 | 支持单用户并发操作 | MVP 阶段 |
| NF-04 | FAISS 索引持久化到本地磁盘 | 重启不丢失 |
| NF-05 | 论文元数据持久化（SQLite 或 JSON） | P0 |

---

## 4. 系统架构

```
Flutter Web (前端)
       ↕ HTTP/REST
FastAPI (后端)
  ├── /upload          # PDF 上传与 Pipeline 触发
  ├── /papers          # 论文列表管理
  ├── /query           # 语义检索 + LLM 问答
  └── /papers/{id}     # 删除论文
       ↕
  ┌────────────┬──────────────┐
  │  FAISS     │  SQLite/JSON │
  │  向量索引   │  元数据存储   │
  └────────────┴──────────────┘
       ↕
  Claude API / Embedding API
```

---

## 5. API 接口概要

| Method | Path | 说明 |
|--------|------|------|
| POST | `/api/upload` | 上传 PDF，触发 ingestion pipeline |
| GET | `/api/papers` | 获取论文列表 |
| DELETE | `/api/papers/{id}` | 删除论文及向量数据 |
| POST | `/api/query` | 提交问题，返回 Answer + Sources |

---

## 6. 数据模型

**Paper（论文）**
```json
{
  "id": "uuid",
  "title": "Attention Is All You Need",
  "filename": "attention.pdf",
  "uploaded_at": "2026-03-09T10:00:00Z",
  "chunk_count": 42,
  "status": "ready"
}
```

> status 枚举值：`uploading` | `processing` | `ready` | `error`

**QueryResponse（问答响应）**
```json
{
  "answer": "The main contribution...",
  "sources": [
    {
      "paper_id": "uuid",
      "paper_title": "Attention Is All You Need",
      "section": "Method",
      "chunk_text": "We propose a new simple network...",
      "score": 0.92
    }
  ]
}
```

---

## 7. 开发阶段规划

| 阶段 | 内容 | 包含功能 |
|------|------|----------|
| MVP | 核心链路跑通 | F-01~04, F-07~13, F-16~19, F-21, F-23 |
| V1.0 | 完善体验 | F-05, F-14, F-15, F-22, F-24, NF-01~05 |
| V1.1 | 增强功能 | F-06, F-20, F-25 |
