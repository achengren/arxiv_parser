"""
Ollama 本地模型适配器
"""

from typing import Dict, Any, Optional, List
from loguru import logger

from arxiv_parser.llm import LLMAdapter, LLMResponse


class OllamaAdapter(LLMAdapter):
    """Ollama 本地模型适配器"""
    
    DEFAULT_BASE_URL = "http://localhost:11434"
    
    def __init__(
        self,
        model: str = "llama3.1",
        base_url: Optional[str] = None,
        **kwargs
    ):
        # Ollama 不需要 API key
        super().__init__(api_key=None, model=model, **kwargs)
        self.base_url = base_url or self.DEFAULT_BASE_URL
        logger.info(f"Ollama adapter initialized with model={model}, url={self.base_url}")
    
    def chat(
        self,
        messages: List[Dict[str, str]],
        **kwargs
    ) -> LLMResponse:
        """发送聊天请求"""
        import requests
        
        response = requests.post(
            f"{self.base_url}/api/chat",
            json={
                "model": self.model,
                "messages": messages,
                "stream": False,
                "options": {
                    "temperature": kwargs.get("temperature", self.temperature),
                    "num_predict": kwargs.get("max_tokens", self.max_tokens),
                }
            },
            timeout=120
        )
        response.raise_for_status()
        data = response.json()
        
        return LLMResponse(
            content=data["message"]["content"],
            model=self.model,
            usage={
                "prompt_tokens": data.get("prompt_eval_count", 0),
                "completion_tokens": data.get("eval_count", 0),
                "total_tokens": data.get("prompt_eval_count", 0) + data.get("eval_count", 0)
            },
            raw_response=data
        )
    
    def complete(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        **kwargs
    ) -> LLMResponse:
        """发送补全请求"""
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        
        return self.chat(messages, **kwargs)
    
    def is_available(self) -> bool:
        """检查 Ollama 服务是否可用"""
        try:
            import requests
            response = requests.get(f"{self.base_url}/api/tags", timeout=5)
            return response.status_code == 200
        except Exception:
            return False
    
    def list_models(self) -> List[str]:
        """列出可用的模型"""
        try:
            import requests
            response = requests.get(f"{self.base_url}/api/tags", timeout=5)
            response.raise_for_status()
            data = response.json()
            return [m["name"] for m in data.get("models", [])]
        except Exception as e:
            logger.error(f"Failed to list models: {e}")
            return []
