"""LLM 客户端工厂：根据配置构建适配器。

将"按配置造 client"的逻辑从 analyzer 中抽离出来，
analyzer 只依赖注入进来的 llm_client，实现解耦。
"""

import os
from typing import Optional

from loguru import logger

from arxiv_parser.llm import LLMAdapter
from .deepseek_adapter import DeepSeekAdapter
from .ollama_adapter import OllamaAdapter


def build_llm_client(config) -> Optional[LLMAdapter]:
    """根据 Config 构建 LLM 客户端；无法构建时返回 None（调用方走 mock）。"""
    llm = config.llm

    if llm.provider == "ollama":
        base_url = llm.base_url or OllamaAdapter.DEFAULT_BASE_URL
        return OllamaAdapter(model=llm.model, base_url=base_url)

    if llm.provider == "deepseek":
        api_key = llm.api_key or os.getenv("DEEPSEEK_API_KEY")
        if api_key:
            return DeepSeekAdapter(
                api_key=api_key,
                model=llm.model,
                temperature=llm.temperature,
                max_tokens=llm.max_tokens,
            )

    logger.warning(f"无法构建 LLM 客户端（provider={llm.provider}），将使用 mock 模式")
    return None
