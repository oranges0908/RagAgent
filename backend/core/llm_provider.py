from abc import ABC, abstractmethod

class LLMProvider(ABC):
    """
    LLM 服务商的抽象基类。

    所有具体实现（Gemini、Claude 等）必须继承此类并实现 complete()。
    QueryService 只依赖此接口，无需关心底层实现。
    """

    @abstractmethod
    async def complete(self, prompt: str) -> str:
        """
        向 LLM 发送 prompt，返回纯文本回复。

        :param prompt: 完整的 prompt 字符串（包含 context + 问题）
        :return:       LLM 生成的回复文本
        :raises:       网络错误或 API 错误时直接抛出，由调用方处理重试
        """
        ...
