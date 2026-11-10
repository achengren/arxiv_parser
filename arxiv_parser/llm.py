"""LLM 端口定义（核心层）

核心域只依赖这个抽象接口，不关心具体实现。
具体适配器（DeepSeek / Ollama）在 adapters/outbound/ 中实现该接口。
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Dict, Any, Optional, List


@dataclass
class LLMResponse:
    """LLM 响应数据结构"""
    content: str
    model: str = ""
    usage: Dict[str, int] = field(default_factory=dict)
    raw_response: Any = None


class LLMAdapter(ABC):
    """LLM 适配器抽象基类（核心端口）"""

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = "",
        temperature: float = 0.3,
        max_tokens: int = 4000,
        **kwargs
    ):
        self.api_key = api_key
        self.model = model
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.extra_kwargs = kwargs

    @abstractmethod
    def chat(self, messages: List[Dict[str, str]], **kwargs) -> LLMResponse:
        """发送聊天请求。"""
        pass

    @abstractmethod
    def complete(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        **kwargs
    ) -> LLMResponse:
        """发送补全请求。"""
        pass

    def is_available(self) -> bool:
        """检查适配器是否可用。"""
        return self.api_key is not None

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(model={self.model})"
