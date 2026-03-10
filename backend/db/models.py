from pydantic import BaseModel


class Paper(BaseModel):
    id: str
    title: str
    filename: str
    uploaded_at: str
    chunk_count: int = 0
    status: str = "processing"
