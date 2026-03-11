import asyncio
import logging
import os

from google import genai
from google.genai import types

from backend.config import GEMINI_MODEL, LLM_MAX_TOKENS
from backend.core.llm_provider import LLMProvider
from backend.core.providers import provider_dict

logger = logging.getLogger(__name__)


class GeminiProvider(LLMProvider):
    """
    Google Gemini LLM 服务商实现。

    需要环境变量 GEMINI_API_KEY。
    """

    def __init__(self, model_name: str = GEMINI_MODEL):
        """
        初始化 Gemini 客户端。

        提示：
        - 从环境变量 GEMINI_API_KEY 读取 API key
        - 调用 genai.configure(api_key=...) 完成全局配置
        - 用 genai.GenerativeModel(model_name) 创建模型实例，存入 self.model
        - 保存 self.model_name 和 self.max_tokens 供 complete() 使用
        """
        api_key = os.environ.get("GEMINI_API_KEY")
        if not api_key:
            raise EnvironmentError("GEMINI_API_KEY environment variable not set")

        # TODO: 调用 genai.configure(api_key=api_key)
        # TODO: self.model = genai.GenerativeModel(model_name)
        self.model_name = model_name
        self.max_tokens = LLM_MAX_TOKENS
        self.client = genai.Client(api_key=api_key)

    async def complete(self, prompt: str) -> str:
        """
        调用 Gemini API，返回生成文本。失败时指数退避重试最多 3 次（1s→2s→4s）。
        """
        last_exc: Exception | None = None
        for attempt in range(3):
            try:
                response = await self.client.aio.models.generate_content(
                    model=self.model_name,
                    contents=prompt,
                    config=types.GenerateContentConfig(
                        max_output_tokens=self.max_tokens,
                    ),
                )
                return response.text
            except Exception as exc:
                last_exc = exc
                wait = 2 ** attempt  # 1s, 2s, 4s
                logger.warning("Gemini API attempt %d failed: %s. Retrying in %ds…", attempt + 1, exc, wait)
                await asyncio.sleep(wait)
        raise RuntimeError(f"Gemini API failed after 3 attempts") from last_exc


provider_dict["gemini"] = GeminiProvider