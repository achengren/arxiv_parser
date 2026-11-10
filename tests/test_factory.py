"""build_llm_client 工厂测试"""

from arxiv_parser.config import Config
from adapters.outbound import build_llm_client, DeepSeekAdapter, OllamaAdapter


def test_build_deepseek_with_key():
    config = Config()
    config.llm.provider = "deepseek"
    config.llm.api_key = "sk-test"
    client = build_llm_client(config)
    assert isinstance(client, DeepSeekAdapter)
    assert client.model == "deepseek-chat"


def test_build_returns_none_without_key(monkeypatch):
    monkeypatch.delenv("DEEPSEEK_API_KEY", raising=False)
    config = Config()
    config.llm.provider = "deepseek"
    config.llm.api_key = None
    assert build_llm_client(config) is None


def test_build_ollama():
    config = Config()
    config.llm.provider = "ollama"
    config.llm.model = "llama3.1"
    client = build_llm_client(config)
    assert isinstance(client, OllamaAdapter)
    assert client.model == "llama3.1"
