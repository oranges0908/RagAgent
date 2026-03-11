from pathlib import Path

# Paths
BASE_DIR = Path(__file__).parent.parent  # project root
STORAGE_DIR = BASE_DIR / "storage"
FAISS_DIR = STORAGE_DIR / "faiss"
DB_PATH = STORAGE_DIR / "papers.db"

# Chunking
CHUNK_SIZE = 500
CHUNK_OVERLAP = 100

# Retrieval
TOP_K = 3

# Embedding
EMBEDDING_MODEL = "all-MiniLM-L6-v2"

# LLM
LLM_PROVIDER="gemini"
GEMINI_MODEL = "gemini-2.0-flash"
LLM_MAX_TOKENS = 1024

# Upload
MAX_UPLOAD_SIZE_MB = 20
MAX_UPLOAD_BYTES = MAX_UPLOAD_SIZE_MB * 1024 * 1024
