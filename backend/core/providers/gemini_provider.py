import os

from google import genai
from google.genai import types

from backend.config import GEMINI_MODEL, LLM_MAX_TOKENS
from backend.core.llm_provider import LLMProvider
from backend.core.providers import provider_dict


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
        调用 Gemini API，返回生成文本。

        提示：
        - 使用 self.model.generate_content_async(prompt, ...)
        - generation_config 可设置 max_output_tokens=self.max_tokens
        - 返回 response.text

        :param prompt: 完整 prompt 字符串
        :return:       Gemini 生成的回复文本
        """
        # TODO: 实现 Gemini API 调用

        response = await self.client.aio.models.generate_content(
            model=self.model_name,
            contents=prompt,
            config=types.GenerateContentConfig(
                max_output_tokens=self.max_tokens,
            )
        )

        return response.text
        raise NotImplementedError


provider_dict["gemini"] = GeminiProvider