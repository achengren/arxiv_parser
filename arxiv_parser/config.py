"""
配置管理模块
"""

import os
import yaml
from pathlib import Path
from typing import Any, Optional
from dataclasses import dataclass, field
from loguru import logger

# 尝试导入 dotenv，如果不可用则跳过
try:
    from dotenv import load_dotenv
    DOTENV_AVAILABLE = True
except ImportError:
    DOTENV_AVAILABLE = False
    logger.warning("python-dotenv not installed, .env file will not be loaded")


def load_env_file(env_path: str = ".env"):
    """
    加载 .env 文件中的环境变量
    
    Args:
        env_path: .env 文件路径
    """
    if not DOTENV_AVAILABLE:
        return
    
    path = Path(env_path)
    if path.exists():
        load_dotenv(path)
        logger.debug(f"Loaded environment from {env_path}")
    else:
        logger.debug(f"No .env file found at {env_path}")


def get_env(key: str, default: Optional[str] = None) -> Optional[str]:
    """
    从环境变量获取值
    
    Args:
        key: 环境变量名
        default: 默认值
        
    Returns:
        环境变量值
    """
    return os.getenv(key, default)


@dataclass
class ArxivConfig:
    """arXiv API 配置"""
    delay_seconds: float = 3.0
    max_results: int = 50
    sort_by: str = "submittedDate"


@dataclass
class PathConfig:
    """路径配置"""
    pdf_dir: str = "output/pdfs"
    image_dir: str = "output/images"
    result_dir: str = "output/results"
    source_dir: str = "output/sources"
    log_dir: str = "logs"
    db_path: str = "output/papers.db"


@dataclass
class LLMConfig:
    """LLM 配置"""
    provider: str = "deepseek"
    model: str = "deepseek-chat"
    api_key: Optional[str] = None
    base_url: Optional[str] = None
    temperature: float = 0.3
    max_tokens: int = 4000


@dataclass
class OutputConfig:
    """输出配置"""
    format: str = "json"
    language: str = "zh"
    include_qa: bool = True
    qa_count: int = 5


@dataclass
class Config:
    """主配置类"""
    arxiv: ArxivConfig = field(default_factory=ArxivConfig)
    paths: PathConfig = field(default_factory=PathConfig)
    llm: LLMConfig = field(default_factory=LLMConfig)
    output: OutputConfig = field(default_factory=OutputConfig)
    
    @classmethod
    def from_yaml(cls, config_path: str = "config/config.yaml") -> "Config":
        """
        从 YAML 文件加载配置
        
        加载顺序：
        1. 默认配置
        2. config.yaml（基础配置）
        3. config.local.yaml（本地覆盖，不上传 Git）
        4. 环境变量（最高优先级）
        """
        # 加载 .env 文件
        load_env_file()
        
        config = cls()
        
        # 1. 加载基础配置
        base_path = Path(config_path)
        if base_path.exists():
            with open(base_path, 'r', encoding='utf-8') as f:
                data = yaml.safe_load(f) or {}
            config._update_from_dict(data)
            logger.debug(f"Loaded base config from {config_path}")
        
        # 2. 加载本地配置（覆盖基础配置）
        local_path = base_path.parent / "config.local.yaml"
        if local_path.exists():
            with open(local_path, 'r', encoding='utf-8') as f:
                local_data = yaml.safe_load(f) or {}
            config._update_from_dict(local_data)
            logger.debug(f"Loaded local config from {local_path}")
        
        # 3. 从环境变量更新 LLM 配置（最高优先级）
        config._update_from_env()
        
        return config
    
    def _update_from_dict(self, data: dict):
        """从字典更新配置"""
        if 'arxiv' in data:
            for key, value in data['arxiv'].items():
                if hasattr(self.arxiv, key):
                    setattr(self.arxiv, key, value)
        
        if 'paths' in data:
            for key, value in data['paths'].items():
                if hasattr(self.paths, key):
                    setattr(self.paths, key, value)
        
        if 'llm' in data:
            for key, value in data['llm'].items():
                if hasattr(self.llm, key):
                    setattr(self.llm, key, value)
        
        if 'output' in data:
            for key, value in data['output'].items():
                if hasattr(self.output, key):
                    setattr(self.output, key, value)
    
    def _update_from_env(self):
        """从环境变量更新配置"""
        # DeepSeek
        if deepseek_key := get_env("DEEPSEEK_API_KEY"):
            if self.llm.provider == "deepseek":
                self.llm.api_key = deepseek_key
                logger.debug("Using DeepSeek API key from environment")
        
        # Ollama
        if ollama_url := get_env("OLLAMA_BASE_URL"):
            self.llm.base_url = ollama_url
            logger.debug(f"Using Ollama base URL: {ollama_url}")
        
        # 日志级别
        if log_level := get_env("LOG_LEVEL"):
            logger.debug(f"Log level from env: {log_level}")
    
    def get(self, key: str, default: Any = None) -> Any:
        """获取配置值，支持点号分隔的嵌套键"""
        keys = key.split('.')
        value = self
        
        for k in keys:
            if hasattr(value, k):
                value = getattr(value, k)
            else:
                return default
        
        return value
    
    def ensure_dirs(self):
        """确保所有输出目录存在"""
        for dir_path in [
            self.paths.pdf_dir,
            self.paths.image_dir,
            self.paths.result_dir,
            self.paths.source_dir,
            self.paths.log_dir
        ]:
            Path(dir_path).mkdir(parents=True, exist_ok=True)
