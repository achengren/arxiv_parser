"""
arXiv Paper Parser - 学术论文解析与知识提取工具
"""

__version__ = "0.3.0"
__author__ = "arXiv Parser Team"

# 配置管理
from .config import Config

# LLM 端口（核心抽象）
from .llm import LLMAdapter, LLMResponse

# 数据模型
from .models import (
    # 基础数据类
    ImageInfo,
    TableInfo,
    Reference,
    QAPair,
    Section,

    # 核心数据流
    PaperMetadata,
    DownloadedPaper,
    ParsedPaper,
    AnalyzedPaper,
    OutputData,
    AnalysisResult,

    # 枚举
    AnalysisType,
    PaperStatus
)

# 数据库管理
from .database import DatabaseManager

# 功能模块
from .fetcher import ArxivFetcher
from .downloader import PaperDownloader
from .parser import ArxivParser
from .analyzer import ArxivAnalyzer
from .exporter import ArxivExporter
from .pipeline import PaperPipeline

# 工具函数
from .utils import (
    parse_arxiv_id,
    normalize_arxiv_id,
    generate_filename,
    is_valid_arxiv_id
)

__all__ = [
    # 版本
    "__version__",

    # 配置
    "Config",

    # LLM 端口
    "LLMAdapter",
    "LLMResponse",

    # 数据模型
    "ImageInfo",
    "TableInfo",
    "Reference",
    "QAPair",
    "Section",
    "PaperMetadata",
    "DownloadedPaper",
    "ParsedPaper",
    "AnalyzedPaper",
    "OutputData",
    "AnalysisResult",
    "AnalysisType",
    "PaperStatus",

    # 数据库
    "DatabaseManager",

    # 功能模块
    "ArxivFetcher",
    "PaperDownloader",
    "ArxivParser",
    "ArxivAnalyzer",
    "ArxivExporter",
    "PaperPipeline",

    # 工具函数
    "parse_arxiv_id",
    "normalize_arxiv_id",
    "generate_filename",
    "is_valid_arxiv_id",
]

# 接口模块在 adapters/ 目录下，需要时单独导入
