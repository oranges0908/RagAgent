from backend.core.llm_provider import LLMProvider
from backend.config import LLM_PROVIDER

# provider_dict 必须在 gemini_provider 导入之前定义，
# 否则 gemini_provider 无法从此模块导入 provider_dict（循环导入）
provider_dict = {}

# 导入各 provider 触发其模块末尾的注册语句（provider_dict["gemini"] = GeminiProvider）
from backend.core.providers import gemini_provider as _  # noqa: E402, F401


def create_llm_provider() -> LLMProvider:
    """
    工厂函数：根据 config.LLM_PROVIDER 创建对应的 LLM 服务商实例。

    如需添加新服务商，只需新建对应 provider 模块并在末尾注册到 provider_dict。
    """
    if LLM_PROVIDER not in provider_dict:
        raise ValueError(f"Unknown LLM provider: {LLM_PROVIDER!r}. Available: {list(provider_dict)}")
    return provider_dict[LLM_PROVIDER]()
