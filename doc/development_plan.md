# AI Research Paper Assistant — Development Plan v1.0

> 本文档是逐步开发的执行依据，按阶段和任务拆解功能需求（来自 PRD）。
> 每个任务完成后在 `[ ]` 中打勾 `[x]`。

---

## 阶段总览

| 阶段 | 目标 | 涉及需求 |
|------|------|----------|
| **MVP** | 核心链路跑通，可上传论文并问答 | F-01~04, F-07~13, F-16~19, F-21, F-23 |
| **V1.0** | 完善体验，多论文管理与性能达标 | F-05, F-14, F-15, F-22, F-24, NF-01~05 |
| **V1.1** | 增强功能，删除与流式输出 | F-06, F-20, F-25 |

---

## MVP — 核心链路

### Step 1：项目脚手架

- [x] 创建 `backend/` 目录，初始化 `requirements.txt`
- [x] 创建 FastAPI app（`main.py`），配置 CORS，启动 uvicorn
- [x] 创建 `backend/config.py`，定义 `chunk_size=500`、`chunk_overlap=100`、`top_k=3`、模型名称、存储路径等常量
- [x] 创建 `storage/faiss/` 和 `storage/` 目录占位文件
- [x] 验证：`uvicorn backend.main:app --reload` 启动无报错，`GET /` 返回 200

---

### Step 2：数据库层（F-04）

> 存储论文元数据

- [x] 安装 `aiosqlite`
- [x] 实现 `db/database.py`：创建 SQLite 连接，建表语句（见 system_design.md §4.1），启用 WAL 模式
- [x] 实现 `db/models.py`：`Paper` Pydantic 模型（id, title, filename, uploaded_at, chunk_count, status）
- [x] 实现 `db/repository.py`：`PaperRepository`
  - [x] `insert(paper) -> Paper`
  - [x] `get_all() -> list[Paper]`
  - [x] `get_by_id(id) -> Paper | None`
  - [x] `update_status(id, status, chunk_count?)`
  - [x] `delete(id)`
- [x] 验证：单元测试 repository CRUD

---

### Step 3：PDF 提取（F-02, F-03）

> 从 PDF 中提取文本和章节结构

- [x] 安装 `pymupdf`
- [x] 实现 `core/pdf_extractor.py`：`PDFExtractor`
  - [x] `extract(file_bytes) -> list[PageSection]`：按页提取文本
  - [x] 启发式章节识别：正则匹配 `Abstract|Introduction|Method|Result|Conclusion|Discussion`（大小写不敏感，独占一行）
  - [x] 若无法识别章节，整篇归为 `"Body"`
- [x] 验证：用示例 PDF 打印提取结果，确认文本完整、章节字段合理

---

### Step 4：文本分块（F-07, F-08）

> 滑动窗口分块，保留来源信息

- [x] 实现 `core/text_chunker.py`：`TextChunker(chunk_size=500, chunk_overlap=100)`
  - [x] `chunk(text, section) -> list[Chunk]`
  - [x] 优先在句子边界（`. ? !` + 空格）切分
  - [x] 每个 `Chunk`：`text, section, chunk_index, char_start, char_end`
- [x] 验证：对已知文本断言 chunk 数量、overlap 字符数、边界不切断单词

---

### Step 5：Embedding 生成（F-09）

> 为 chunk 生成向量

- [x] 安装 `sentence-transformers`
- [x] 实现 `core/embedder.py`：`Embedder`
  - [x] `__init__(model_name)`：加载模型，记录 `dim`
  - [x] `embed(texts: list[str]) -> np.ndarray`：批量 embed，batch_size=32
- [x] 验证：embed 5 条文本，返回 shape `(5, dim)`，值为 float32

---

### Step 6：FAISS 存储（F-10, F-11）

> 持久化向量索引与 chunk 元数据

- [x] 安装 `faiss-cpu`
- [x] 实现 `core/faiss_store.py`：`FAISSStore`
  - [x] `add(paper_id, vectors, metadata_list)`：写入内存索引 + meta list
  - [x] `save(paper_id)`：写 `{paper_id}.index` 和 `{paper_id}.meta.json`
  - [x] `load(paper_id)`：从磁盘读入缓存
  - [x] `search(query_vector, top_k, paper_id?) -> list[SearchResult]`
  - [x] 启动时扫描 `storage/faiss/` 自动 load 所有 index
- [x] 验证：add → save → 重启 → load → search，结果一致

---

### Step 7：摄入 Pipeline（F-01, F-02, F-07~F-11）

> 将 PDF 上传到 FAISS + SQLite

- [x] 实现 `services/ingestion.py`：`IngestionService`
  - [x] `ingest(file_bytes, filename) -> Paper`
    1. 生成 UUID，创建 DB 记录（status=`processing`）
    2. PDF 提取 → 分块 → embed → FAISSStore.add + save
    3. 更新 DB（status=`ready`, chunk_count）
    4. 任何步骤失败 → 更新 status=`error`，重新抛出
- [x] 实现 `routers/upload.py`：`POST /api/upload`
  - [x] 接受 `multipart/form-data`，文件类型校验（`.pdf`），大小限制 20MB
  - [x] 调用 `IngestionService.ingest()`，返回 `Paper`
- [x] 安装 `python-multipart`
- [x] 验证：上传真实 PDF，检查 DB 记录和 `.index` 文件生成

---

### Step 8：LLM 代理层 + Gemini 问答（F-16~F-19）

> 引入 LLMProvider 抽象层，默认使用 Gemini；检索 chunk，构建 Prompt，调用 LLM

- [x] 安装 `google-generativeai`
- [x] 实现 `core/llm_provider.py`：`LLMProvider` 抽象基类
  - [x] `async complete(prompt: str) -> str`
- [x] 实现 `core/providers/gemini_provider.py`：`GeminiProvider(LLMProvider)`
  - [ ] `__init__`：读取 `GEMINI_API_KEY`，初始化 `genai` 客户端
  - [ ] `complete(prompt) -> str`：调用 `generate_content_async`，返回 `response.text`
- [x] 实现 `core/providers/__init__.py`：`create_llm_provider()` 工厂函数
- [x] 实现 `core/prompt_builder.py`：`PromptBuilder`
  - [ ] `build(chunks, question) -> str`：生成编号 context 块 + 问题（见 system_design.md §6.4）
  - [ ] context 超长时按比例截断，总长不超过 ~3000 tokens
- [x] 实现 `services/query_service.py`：`QueryService`
  - [x] `query(question, paper_id?) -> QueryResponse`
    1. embed question
    2. FAISSStore.search(top_k=3, paper_id?)
    3. PromptBuilder.build()
    4. LLMProvider.complete(prompt)，`max_tokens=1024`
    5. 解析返回文本，组装 `QueryResponse`
- [x] 实现 `routers/query.py`：`POST /api/query`
  - [x] 校验 `question` 非空；若指定 `paper_id` 校验论文存在
  - [x] 返回 `{answer, sources}`
- [x] 更新 `main.py`：注册全局 `embedder` 和 `llm_provider` 实例，引入 query router
- [x] 验证：用上传的论文提问，返回 answer 和 sources

---

### Step 9：Flutter MVP 前端（F-21, F-23）

> 上传页 + 问答页

- [ ] 初始化 Flutter Web 项目（`frontend/`）
- [ ] 添加依赖：`http`、`file_picker`、`flutter_markdown`
- [ ] 实现 `services/api_service.dart`：封装 `upload(file)`、`query(question, paperId?)`
- [ ] 实现 `pages/upload_page.dart`
  - [ ] 点击选择 PDF 文件（file_picker）
  - [ ] 调用 upload API，展示上传进度和结果（paper title / error）
- [ ] 实现 `pages/query_page.dart`
  - [ ] 文本输入框 + 提交按钮
  - [ ] 展示 Answer（Markdown 渲染）和 Sources 列表（paper, section, quote）
- [ ] 实现 `main.dart`：简单 Tab/导航，切换两页
- [ ] 验证：端到端跑通——上传论文 → 切换到问答页 → 提问 → 看到答案

---

## V1.0 — 完善体验

### Step 10：论文列表（F-05）

- [ ] 实现 `routers/papers.py`：`GET /api/papers`，返回按 `uploaded_at DESC` 排序的论文列表
- [ ] Flutter `pages/papers_page.dart`：展示论文列表（title, filename, chunk_count, status）
- [ ] 导航加入论文列表页（Tab 或侧边栏）

---

### Step 11：按论文过滤检索（F-14, F-15）

- [ ] `FAISSStore.search()` 支持 `paper_id` 过滤（已有设计，补全逻辑）
- [ ] `POST /api/query` 的 `paper_id` 字段完整联通（MVP 中可能是 optional）
- [ ] `SearchResult` 包含 `score` 字段（余弦相似度或 L2 距离归一化）
- [ ] API 响应中 `sources[].score` 正确输出（F-15）

---

### Step 12：前端选择论文提问（F-24）

- [ ] `query_page.dart` 增加论文选择下拉框（从 papers 列表动态加载）
- [ ] 选择"全库"时 `paper_id` 为 null

---

### Step 13：非功能达标（NF-01~05）

- [ ] NF-01 验证：用 `time curl` 测量 `/api/papers` 和 `/api/query`（仅检索部分）延迟 < 500ms
- [ ] NF-02 验证：完整问答端到端 < 10s（主要取决于 LLM 响应）
- [ ] NF-04 验证：重启后 FAISS 索引自动加载，search 正常
- [ ] NF-05 验证：重启后 SQLite 论文记录完整
- [ ] 外部 API（Embedding / Claude）重试逻辑：3次，指数退避（1s→2s→4s）
- [ ] 全局异常处理器：未捕获异常返回 500 + 日志

---

## V1.1 — 增强功能

### Step 14：删除论文（F-06）

- [ ] `routers/papers.py`：`DELETE /api/papers/{id}`
  - [ ] 校验论文存在，返回 404 if not
  - [ ] SQLite delete
  - [ ] 删除 `{id}.index` 和 `{id}.meta.json`
  - [ ] FAISSStore 从内存缓存中移除
  - [ ] 返回 204
- [ ] Flutter `papers_page.dart`：每条论文右侧加删除按钮，二次确认弹窗

---

### Step 15：流式输出（F-20）

- [ ] Claude API 调用改为 `stream=True`
- [ ] FastAPI 使用 `StreamingResponse`，Content-Type: `text/event-stream`
- [ ] Flutter `query_page.dart` 改用 `http` chunked 读取或 SSE，逐字渲染答案

---

### Step 16：Sources 折叠展开（F-25）

- [ ] Flutter `query_page.dart`：Sources 区域默认折叠，点击展开显示原文摘录
- [ ] 高亮 `chunk_text` 中与问题相关的关键词（可选，客户端简单实现）

---

## 附：需求编号索引

| 需求 | 说明 | 对应 Step |
|------|------|-----------|
| F-01 | PDF 上传 | Step 7 |
| F-02 | PDF 文本提取 | Step 3, 7 |
| F-03 | 章节识别 | Step 3 |
| F-04 | 论文元数据存储 | Step 2 |
| F-05 | 论文列表 | Step 10 |
| F-06 | 删除论文 | Step 14 |
| F-07 | 文本分块 | Step 4 |
| F-08 | chunk_size/overlap 参数 | Step 4 |
| F-09 | Embedding 生成 | Step 5 |
| F-10 | FAISS 存储 | Step 6 |
| F-11 | chunk 来源元数据 | Step 6 |
| F-12 | 问题 Embedding | Step 8 |
| F-13 | FAISS 向量检索 top_k=3 | Step 8 |
| F-14 | 按论文过滤检索 | Step 11 |
| F-15 | 相似度分数 | Step 11 |
| F-16 | chunks 拼接上下文调用 LLM | Step 8 |
| F-17 | Prompt 模板 | Step 8 |
| F-18 | 结构化输出 Answer + Sources | Step 8 |
| F-19 | Sources 含论文名/章节/摘录 | Step 8 |
| F-20 | 流式输出 | Step 15 |
| F-21 | 上传页 | Step 9 |
| F-22 | 论文列表页 | Step 10 |
| F-23 | 问答页 | Step 9 |
| F-24 | 选择论文提问 | Step 12 |
| F-25 | Sources 折叠展开 | Step 16 |
| NF-01~05 | 非功能需求 | Step 13 |
