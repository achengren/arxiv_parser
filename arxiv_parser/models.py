"""
数据模型定义
定义整个系统的数据结构和流转格式
"""

from dataclasses import dataclass, field, asdict
from typing import List, Dict, Optional, Any
from datetime import datetime
from enum import Enum


class AnalysisType(Enum):
    """分析类型枚举"""
    SUMMARY = "summary"
    INNOVATION = "innovation"
    KEYWORDS = "keywords"
    METHODOLOGY = "methodology"
    EXPERIMENTS = "experiments"
    QA_GENERATION = "qa_generation"
    CONCLUSIONS = "conclusions"
    NOVELTY_SCORING = "novelty_scoring"


class PaperStatus(Enum):
    """单个处理阶段的状态"""
    PENDING = "pending"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class ImageInfo:
    """图片信息"""
    image_id: int
    page_number: int
    local_path: str
    caption: Optional[str] = None
    width: Optional[int] = None
    height: Optional[int] = None
    description: Optional[str] = None  # LLM 生成的图片描述


@dataclass
class TableInfo:
    """表格信息"""
    table_id: int
    page_number: int
    caption: Optional[str] = None
    data: Optional[List[List[str]]] = None  # 表格数据（二维数组）
    markdown: Optional[str] = None  # Markdown 格式


@dataclass
class Reference:
    """参考文献"""
    ref_id: str
    text: str
    url: Optional[str] = None
    doi: Optional[str] = None


@dataclass
class QAPair:
    """问答对"""
    question: str
    answer: str
    qa_type: str = "general"  # general/innovation/methodology/experiment


@dataclass
class PaperMetadata:
    """
    论文元数据（从 arXiv API 获取）
    对应 fetcher.py 的输出
    """
    arxiv_id: str
    title: str
    authors: List[str]
    abstract: str
    categories: List[str]
    primary_category: str
    published_date: str
    updated_date: str
    pdf_url: str
    entry_id: str
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return asdict(self)


@dataclass
class DownloadedPaper:
    """
    下载后的论文
    对应 downloader.py 的输出
    """
    metadata: PaperMetadata
    local_pdf_path: str
    download_time: str = field(default_factory=lambda: datetime.now().isoformat())
    file_size: Optional[int] = None  # 文件大小（字节）
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return asdict(self)


@dataclass
class Section:
    """论文章节"""
    name: str
    content: str
    level: int = 1  # 章节层级（1=一级标题，2=二级标题...）
    start_page: Optional[int] = None
    end_page: Optional[int] = None


@dataclass
class ParsedPaper:
    """
    解析后的论文（PDF 解析结果）
    对应 parser.py 的输出
    """
    downloaded: DownloadedPaper
    
    # 文本内容
    full_text: str = ""
    sections: List[Section] = field(default_factory=list)
    
    # 结构化元素
    images: List[ImageInfo] = field(default_factory=list)
    tables: List[TableInfo] = field(default_factory=list)
    references: List[Reference] = field(default_factory=list)
    
    # 元信息
    page_count: int = 0
    parse_time: str = field(default_factory=lambda: datetime.now().isoformat())
    parse_errors: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return asdict(self)


@dataclass
class AnalyzedPaper:
    """
    分析后的论文（LLM 分析结果）
    对应 analyzer.py 的输出
    """
    parsed: ParsedPaper
    
    # 分析结果
    summary_zh: str = ""  # 中文摘要
    summary_en: str = ""  # 英文摘要
    
    innovations: List[str] = field(default_factory=list)  # 创新点列表
    methodology: str = ""  # 核心方法
    experiments: str = ""  # 实验设置和结果
    conclusions: str = ""  # 主要结论
    
    # 评分
    novelty_score: Optional[int] = None  # 新颖性评分 1-5
    quality_score: Optional[int] = None  # 质量评分 1-5
    
    # 问答对
    qa_pairs: List[QAPair] = field(default_factory=list)
    
    # 关键词
    keywords: List[str] = field(default_factory=list)
    
    # 分析元信息
    analysis_time: str = field(default_factory=lambda: datetime.now().isoformat())
    llm_model: str = ""
    analysis_errors: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return asdict(self)


@dataclass
class OutputData:
    """
    最终输出格式
    对应 exporter.py 的输出
    """
    # 基本信息
    title: str
    arxiv_id: str
    categories: List[str]
    source_url: str
    pdf_path: str

    # 全文
    full_text: str = ""

    # 结构化知识
    structured_knowledge: Dict[str, Any] = field(default_factory=dict)
    # 包含：作者、机构、发表日期、研究方向、核心方法、数据集、主要贡献等
    
    # 段落内容
    sections: Dict[str, Any] = field(default_factory=dict)
    # 包含：摘要、正文各章节（引言、方法、实验、结论等）
    
    # 图片和表格
    images: List[Dict[str, Any]] = field(default_factory=list)
    tables: List[Dict[str, Any]] = field(default_factory=list)
    
    # 参考文献
    references: Dict[str, Any] = field(default_factory=dict)
    
    # LLM 分析结果
    analysis: Dict[str, Any] = field(default_factory=dict)
    # 包含：创新点、技术亮点、实验结论、问答对等
    
    # 元信息
    process_time: str = field(default_factory=lambda: datetime.now().isoformat())
    version: str = "1.0"
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典（最终 JSON 格式，统一使用英文键）"""
        return asdict(self)
    
    def to_json(self, indent: int = 2) -> str:
        """转换为 JSON 字符串"""
        import json
        return json.dumps(self.to_dict(), indent=indent, ensure_ascii=False)


@dataclass
class AnalysisResult:
    """
    分析结果（从数据库读取）
    用于缓存和快速查询，避免重复调用 LLM
    """
    arxiv_id: str
    llm_model: str
    
    # 摘要
    summary_zh: str = ""
    summary_en: str = ""
    
    # 分析内容
    innovations: List[str] = field(default_factory=list)
    methodology: str = ""
    experiments: str = ""
    conclusions: str = ""
    
    # 评分
    novelty_score: Optional[int] = None
    quality_score: Optional[int] = None
    
    # 关键词
    keywords: List[str] = field(default_factory=list)
    
    # 问答对
    qa_pairs: List[QAPair] = field(default_factory=list)
    
    # 元信息
    analysis_time: str = ""
    created_at: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return asdict(self)
