# AI Research Paper Assistant — System Design v1.0

## 1. Overall Architecture

```
┌─────────────────────────────────────────┐
│           Flutter Web (Frontend)         │
│  ┌──────────┐ ┌──────────┐ ┌─────────┐  │
│  │  Upload  │ │  Papers  │ │   Q&A   │  │
│  │   Page   │ │   List   │ │  Page   │  │
│  └──────────┘ └──────────┘ └─────────┘  │
└─────────────────┬───────────────────────┘
                  │ HTTP/REST (JSON)
┌─────────────────▼───────────────────────┐
│           FastAPI Backend                │
│  ┌──────────┐ ┌──────────┐ ┌─────────┐  │
│  │ /upload  │ │ /papers  │ │ /query  │  │
│  └────┬─────┘ └────┬─────┘ └────┬────┘  │
│       │            │            │        │
│  ┌────▼────────────▼────────────▼─────┐  │
│  │         Service Layer               │  │
│  │  IngestionService  QueryService    │  │
│  └────┬──────────────────────┬────────┘  │
│       │                      │           │
│  ┌────▼──────┐  ┌────────────▼────────┐  │
│  │ FAISSStore│  │   SQLiteRepository  │  │
│  └────┬──────┘  └────────────┬────────┘  │
│       │                      │           │
│    faiss/                 papers.db      │
│    *.index                               │
└──────────────────┬──────────────────────┘
                   │ HTTPS
        ┌──────────▼──────────┐
        │  External APIs       │
        │  Claude API (LLM)   │
        │  Embedding API      │
        └─────────────────────┘
```

---

## 2. Directory Structure

```
RagAgent/
├── backend/
│   ├── main.py                  # FastAPI app entry point, CORS config
│   ├── config.py                # Settings (chunk size, model names, paths)
│   ├── routers/
│   │   ├── upload.py            # POST /api/upload
│   │   ├── papers.py            # GET /api/papers, DELETE /api/papers/{id}
│   │   └── query.py             # POST /api/query
│   ├── services/
│   │   ├── ingestion.py         # IngestionService: PDF → chunks → FAISS
│   │   └── query.py             # QueryService: question → retrieval → LLM
│   ├── core/
│   │   ├── pdf_extractor.py     # PyMuPDF-based text + section extraction
│   │   ├── text_chunker.py      # TextChunker: sliding-window chunking
│   │   ├── embedder.py          # Embedding generation (local or OpenAI)
│   │   ├── faiss_store.py       # FAISSStore: index CRUD + persistence
│   │   └── prompt_builder.py    # PromptBuilder: context → prompt string
│   ├── db/
│   │   ├── database.py          # SQLite connection (aiosqlite)
│   │   ├── models.py            # Paper dataclass / Pydantic models
│   │   └── repository.py        # PaperRepository: CRUD on papers table
│   └── storage/
│       ├── faiss/               # *.index files, one per paper
│       └── papers.db            # SQLite database file
├── frontend/                    # Flutter Web project
│   ├── lib/
│   │   ├── main.dart
│   │   ├── pages/
│   │   │   ├── upload_page.dart
│   │   │   ├── papers_page.dart
│   │   │   └── query_page.dart
│   │   └── services/
│   │       └── api_service.dart  # HTTP client wrapper
│   └── pubspec.yaml
├── doc/
│   ├── product_requirement_document.md
│   └── system_design.md
└── requirements.txt
```

---

## 3. Core Runtime Flows

### 3.1 Upload / Ingestion Pipeline

```
Client                  FastAPI              IngestionService         External
  │                        │                        │                    │
  │── POST /api/upload ───►│                        │                    │
  │   (multipart PDF)      │── validate file ──────►│                    │
  │                        │                        │── extract text ───►│
  │                        │                        │   (PyMuPDF)        │
  │                        │                        │◄── raw text ───────│
  │                        │                        │                    │
  │                        │                        │── detect sections  │
  │                        │                        │── chunk text       │
  │                        │                        │   (size=500,       │
  │                        │                        │    overlap=100)    │
  │                        │                        │                    │
  │                        │                        │── embed chunks ───►│
  │                        │                        │   (Embedding API)  │
  │                        │                        │◄── vectors ────────│
  │                        │                        │                    │
  │                        │                        │── FAISSStore.add() │
  │                        │                        │── save .index file │
  │                        │                        │── SQLite insert    │
  │◄── 200 {paper_id} ─────│◄── paper metadata ─────│                    │
```

### 3.2 Query Flow

```
Client                  FastAPI              QueryService            External
  │                        │                     │                      │
  │── POST /api/query ────►│                     │                      │
  │   {question,           │── validate ────────►│                      │
  │    paper_id?}          │                     │── embed question ───►│
  │                        │                     │◄── query vector ─────│
  │                        │                     │                      │
  │                        │                     │── FAISSStore.search()│
  │                        │                     │   top_k=3 chunks     │
  │                        │                     │                      │
  │                        │                     │── PromptBuilder      │
  │                        │                     │   .build(chunks,     │
  │                        │                     │          question)   │
  │                        │                     │                      │
  │                        │                     │── Claude API call ──►│
  │                        │                     │◄── answer text ──────│
  │                        │                     │                      │
  │◄── 200 {answer,        │◄── QueryResponse ───│                      │
  │         sources} ──────│                     │                      │
```

---

## 4. Data Storage Design

### 4.1 SQLite Schema

```sql
CREATE TABLE papers (
    id          TEXT PRIMARY KEY,          -- UUID v4
    title       TEXT NOT NULL,             -- extracted or filename-derived
    filename    TEXT NOT NULL,             -- original uploaded filename
    uploaded_at TEXT NOT NULL,             -- ISO 8601 timestamp
    chunk_count INTEGER NOT NULL DEFAULT 0,
    status      TEXT NOT NULL DEFAULT 'processing'
                CHECK(status IN ('uploading','processing','ready','error'))
);
```

**Index:** `CREATE INDEX idx_papers_uploaded_at ON papers(uploaded_at DESC);`

### 4.2 FAISS Index Design

- One FAISS `IndexFlatL2` per paper, stored at `storage/faiss/{paper_id}.index`
- A parallel metadata file `storage/faiss/{paper_id}.meta.json` stores chunk records:

```json
[
  {
    "chunk_index": 0,
    "paper_id": "uuid",
    "paper_title": "Attention Is All You Need",
    "section": "Abstract",
    "text": "We propose a new simple network architecture..."
  }
]
```

- On query with `paper_id` filter: load only that paper's index. Without filter: merge top-k results across all loaded indexes.
- Indexes are loaded lazily and cached in memory during the process lifetime.

---

## 5. API Interface Specification

### POST /api/upload

**Request:** `multipart/form-data`
- `file`: PDF binary (max 20 MB)

**Response 200:**
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "title": "Attention Is All You Need",
  "filename": "attention.pdf",
  "uploaded_at": "2026-03-09T10:00:00Z",
  "chunk_count": 42,
  "status": "ready"
}
```

**Errors:**
- `400` — not a PDF / file too large
- `422` — validation error
- `500` — ingestion pipeline failure

---

### GET /api/papers

**Response 200:**
```json
[
  {
    "id": "...",
    "title": "...",
    "filename": "...",
    "uploaded_at": "...",
    "chunk_count": 42,
    "status": "ready"
  }
]
```

---

### DELETE /api/papers/{id}

**Response 204:** No content

**Errors:**
- `404` — paper not found

**Side effects:** Removes SQLite row and deletes `{id}.index` + `{id}.meta.json`.

---

### POST /api/query

**Request:**
```json
{
  "question": "What is the main contribution of this paper?",
  "paper_id": "550e8400-e29b-41d4-a716-446655440000"
}
```
`paper_id` is optional; omit to search across all papers.

**Response 200:**
```json
{
  "answer": "The main contribution of the paper is introducing the Transformer architecture...",
  "sources": [
    {
      "paper_id": "uuid",
      "paper_title": "Attention Is All You Need",
      "section": "Method",
      "chunk_text": "We propose a new simple network architecture, the Transformer...",
      "score": 0.92
    }
  ]
}
```

**Errors:**
- `400` — empty question
- `404` — paper_id not found (when specified)
- `502` — Claude API or Embedding API unreachable

---

## 6. Key Component Design

### 6.1 TextChunker

```
TextChunker(chunk_size=500, chunk_overlap=100)
  .chunk(text: str, section: str) -> list[Chunk]
```

- Uses character-level sliding window.
- Splits on sentence boundaries when possible (`.`, `?`, `!` followed by whitespace) to avoid cutting mid-sentence.
- Falls back to hard split at `chunk_size` if no boundary found within the last 100 characters.
- Each `Chunk` carries: `text`, `section`, `chunk_index`, `char_start`, `char_end`.

### 6.2 FAISSStore

```
FAISSStore
  .add(paper_id, vectors, metadata) -> None
  .search(query_vector, top_k, paper_id?) -> list[SearchResult]
  .delete(paper_id) -> None
  .save(paper_id) -> None   # writes .index + .meta.json
  .load(paper_id) -> None   # reads from disk into cache
```

- Embedding dimension fixed at model init time (e.g., 384 for `all-MiniLM-L6-v2`).
- `IndexFlatL2` for exact search (suitable for MVP scale; upgrade to `IndexIVFFlat` if > 100k chunks).
- Thread-safe reads; writes protected by a per-paper asyncio lock.

### 6.3 PromptBuilder

```
PromptBuilder.build(chunks: list[SearchResult], question: str) -> str
```

Produces:

```
Use the following context to answer the question.

Context:
[1] (Attention Is All You Need — Method)
We propose a new simple network architecture, the Transformer...

[2] (Attention Is All You Need — Introduction)
...

Question:
What is the main contribution of this paper?

Answer clearly and cite the source text.
```

- Context sections are numbered `[1]`, `[2]`, `[3]` to allow the LLM to reference them.
- Total prompt length is capped at ~3000 tokens; chunks are truncated proportionally if needed.

---

## 7. Error Handling Strategy

| Layer | Strategy |
|-------|----------|
| Router | FastAPI `HTTPException` with structured `{"detail": "..."}` body |
| IngestionService | On any step failure, set `paper.status = "error"` in DB; raise to router |
| FAISSStore | `FileNotFoundError` on missing index → `404` propagation |
| Embedding API | Retry up to 3× with exponential backoff (1s, 2s, 4s); then `502` |
| Claude API | Same retry policy; surface as `502` if all retries exhausted |
| PDF extraction | If text extraction yields < 100 chars, reject with `400 "Could not extract text from PDF"` |

All unhandled exceptions are caught by a global FastAPI `exception_handler` that logs the traceback and returns `500`.

---

## 8. Non-Functional Design

### 8.1 Performance

- Embedding generation is the bottleneck; batching chunks (batch size 32) reduces API round-trips.
- FAISS search is in-process (no network); latency < 10ms for indexes up to ~10k vectors.
- Target: non-LLM API path < 500ms (NF-01); end-to-end < 10s (NF-02).

### 8.2 Persistence

- FAISS indexes are written to disk immediately after each upload completes (`FAISSStore.save()`).
- SQLite uses WAL mode (`PRAGMA journal_mode=WAL`) for safe concurrent reads during writes.
- On startup, `FAISSStore` scans `storage/faiss/` and pre-loads all `*.index` files into memory.

### 8.3 CORS

FastAPI `CORSMiddleware` configured for development:
```python
allow_origins=["http://localhost:*"]
allow_methods=["GET", "POST", "DELETE"]
allow_headers=["*"]
```
Production: restrict `allow_origins` to the deployed Flutter Web origin.

---

## 9. Technology Dependencies

| Package | Version | Purpose |
|---------|---------|---------|
| `fastapi` | ≥ 0.110 | Web framework |
| `uvicorn` | ≥ 0.29 | ASGI server |
| `pymupdf` (fitz) | ≥ 1.23 | PDF text extraction |
| `faiss-cpu` | ≥ 1.8 | Vector similarity search |
| `sentence-transformers` | ≥ 2.6 | Local embedding model |
| `anthropic` | ≥ 0.25 | Claude API client |
| `aiosqlite` | ≥ 0.20 | Async SQLite access |
| `python-multipart` | ≥ 0.0.9 | File upload support |
| `pydantic` | ≥ 2.0 | Request/response validation |

Flutter dependencies: `http`, `file_picker`, `flutter_markdown`.
