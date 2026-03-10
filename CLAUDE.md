# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

RagAgent is an AI Research Paper Assistant — a RAG-based (Retrieval-Augmented Generation) web application. Users upload PDF research papers and ask natural language questions, receiving AI-generated answers with citations.

**Tech Stack:**
- Backend: Python + FastAPI
- Vector DB: FAISS (per-paper `.index` + `.meta.json` files)
- LLM: Claude API (`claude-sonnet-4-6`)
- Embeddings: Sentence Transformers
- Metadata: SQLite via aiosqlite
- Frontend: Flutter Web

## Commands

*(No source code exists yet — the project is in planning phase. Update this section as implementation progresses.)*

**Backend (planned):**
```bash
cd backend
pip install -r requirements.txt
uvicorn main:app --reload
```

**Frontend (planned):**
```bash
cd frontend
flutter pub get
flutter run -d web
```

## Architecture

### Data Flow

```
PDF Upload → PDFExtractor → TextChunker → Embedder → FAISSStore + SQLite
User Question → Embedder → FAISSStore (top-K search) → PromptBuilder → Claude API → Answer + Citations
```

### Backend Structure (planned)

- **IngestionService** — orchestrates the upload pipeline (PDF → chunks → embeddings → FAISS)
- **QueryService** — handles question embedding, vector search, LLM call, response assembly
- **PDFExtractor** — text extraction with section detection (Abstract, Introduction, Methods, etc.)
- **TextChunker** — sliding-window chunking (500-char chunks, 100-char overlap)
- **Embedder** — sentence-transformers embedding generation
- **FAISSStore** — `IndexFlatL2` index, one per paper; pre-loaded on startup
- **PromptBuilder** — constructs numbered context sections ([1], [2], …) for citation tracking

### Storage

- SQLite: paper metadata (`id`, `title`, `filename`, `upload_time`, `chunk_count`, `status`)
- FAISS: `{paper_id}.index` + `{paper_id}.meta.json` (written immediately after ingestion)

### API Endpoints

| Method | Path | Purpose |
|--------|------|---------|
| POST | `/api/upload` | Upload PDF, trigger ingestion |
| GET | `/api/papers` | List all papers |
| DELETE | `/api/papers/{id}` | Delete paper and vectors |
| POST | `/api/query` | Ask a question, get answer + sources |

## Key Design Decisions

- FAISS `IndexFlatL2` for exact search (upgrade to `IndexIVFFlat` if vector count exceeds ~10k)
- Retry logic: 3 attempts with exponential backoff for Claude API calls
- MVP is single-user; multi-user support is a later phase
- Performance targets: API < 500ms (excluding LLM), end-to-end Q&A < 10s

## Reference Docs

- `doc/product_requirement.md` — full PRD
- `doc/system_design.md` — technical architecture and data models
- `doc/development_plan.md` — 16-step phased implementation plan
