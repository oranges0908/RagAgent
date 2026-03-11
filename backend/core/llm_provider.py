from abc import ABC, abstractmethod
from typing import AsyncIterator

class LLMProvider(ABC):
    """
    LLM 服务商的抽象基类。
    """

    @abstractmethod
    async def complete(self, prompt: str) -> str:
        """向 LLM 发送 prompt，返回完整回复文本。"""
        ...

    @abstractmethod
    async def complete_stream(self, prompt: str) -> AsyncIterator[str]:
        """向 LLM 发送 prompt，逐块 yield 回复文本片段。"""
        ...
