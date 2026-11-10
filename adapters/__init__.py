"""
接口模块 - 负责与外部系统交互

包含两类适配器：
- outbound: 本系统调用外部服务（如 LLM API）
- inbound: 本系统被外部调用（如 MCP 工具）
"""

from .outbound import LLMAdapter, LLMResponse, DeepSeekAdapter, OllamaAdapter

__all__ = [
    "LLMAdapter",
    "LLMResponse",
    "DeepSeekAdapter",
    "OllamaAdapter",
]
