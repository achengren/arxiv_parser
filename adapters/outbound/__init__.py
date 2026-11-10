"""
Outbound Adapters - 本系统调用外部服务
"""

from arxiv_parser.llm import LLMAdapter, LLMResponse
from .deepseek_adapter import DeepSeekAdapter
from .ollama_adapter import OllamaAdapter
from .factory import build_llm_client

__all__ = [
    "LLMAdapter",
    "LLMResponse",
    "DeepSeekAdapter",
    "OllamaAdapter",
    "build_llm_client",
]
