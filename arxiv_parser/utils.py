"""
工具函数模块
"""

import re
from typing import Optional
from pathlib import Path


def parse_arxiv_id(input_str: str) -> Optional[str]:
    """
    从各种格式中提取纯 arXiv ID
    
    支持的格式:
    - 纯 ID: "2301.12345" 或 "2301.12345v1"
    - abs URL: "https://arxiv.org/abs/2301.12345"
    - pdf URL: "https://arxiv.org/pdf/2301.12345.pdf"
    
    Args:
        input_str: 输入字符串
        
    Returns:
        纯 arXiv ID（不含版本号）或 None
    """
    if not input_str:
        return None
    
    input_str = input_str.strip()
    
    # 从 URL 中提取
    if "/abs/" in input_str:
        match = re.search(r'/abs/([0-9]+\.[0-9]+)', input_str)
        if match:
            return match.group(1)
    
    if "/pdf/" in input_str:
        match = re.search(r'/pdf/([0-9]+\.[0-9]+)', input_str)
        if match:
            return match.group(1)
    
    # 纯 ID 格式
    match = re.match(r'^([0-9]+\.[0-9]+)(v\d+)?$', input_str)
    if match:
        return match.group(1)
    
    return None


def normalize_arxiv_id(arxiv_id: str) -> str:
    """
    标准化 arXiv ID（保留版本号）

    Args:
        arxiv_id: arXiv ID 或 abs/pdf URL

    Returns:
        标准化 ID（含版本号）
    """
    arxiv_id = arxiv_id.strip()

    # 从 URL 提取（保留版本号）
    for sep in ("/abs/", "/pdf/"):
        if sep in arxiv_id:
            match = re.search(re.escape(sep) + r'([0-9]+\.[0-9]+(?:v\d+)?)', arxiv_id)
            if match:
                return match.group(1)

    return arxiv_id


def generate_filename(
    arxiv_id: str,
    author: Optional[str] = None,
    year: Optional[str] = None,
    extension: str = ".pdf"
) -> str:
    """
    生成标准化的文件名
    
    Args:
        arxiv_id: arXiv ID
        author: 第一作者姓氏
        year: 年份
        extension: 文件扩展名
        
    Returns:
        文件名（含扩展名）
    """
    parts = []
    
    if year:
        parts.append(str(year))
    
    if author:
        # 清理作者名字
        clean_author = re.sub(r'[^\w\s-]', '', author)
        clean_author = clean_author.split()[-1] if clean_author else "unknown"
        parts.append(clean_author)
    
    # 清理 ID 中的斜杠
    clean_id = arxiv_id.replace("/", "_")
    parts.append(clean_id)
    
    return "_".join(parts) + extension


def ensure_dir(path: str) -> Path:
    """
    确保目录存在
    
    Args:
        path: 目录路径
        
    Returns:
        Path 对象
    """
    p = Path(path)
    p.mkdir(parents=True, exist_ok=True)
    return p


def truncate_text(text: str, max_length: int = 100, suffix: str = "...") -> str:
    """
    截断文本
    
    Args:
        text: 原始文本
        max_length: 最大长度
        suffix: 截断后缀
        
    Returns:
        截断后的文本
    """
    if len(text) <= max_length:
        return text
    return text[:max_length - len(suffix)] + suffix


def clean_text(text: str) -> str:
    """
    清理文本（去除多余空白、换行等）
    
    Args:
        text: 原始文本
        
    Returns:
        清理后的文本
    """
    # 替换多个空白字符为单个空格
    text = re.sub(r'\s+', ' ', text)
    # 去除首尾空白
    text = text.strip()
    return text


def format_authors(authors: list, max_authors: int = 3) -> str:
    """
    格式化作者列表
    
    Args:
        authors: 作者列表
        max_authors: 最多显示作者数
        
    Returns:
        格式化后的作者字符串
    """
    if not authors:
        return ""
    
    if len(authors) <= max_authors:
        return ", ".join(authors)
    
    return ", ".join(authors[:max_authors]) + f" 等{len(authors)}人"


def is_valid_arxiv_id(arxiv_id: str) -> bool:
    """
    检查是否为有效的 arXiv ID
    
    Args:
        arxiv_id: arXiv ID
        
    Returns:
        是否有效
    """
    pattern = r'^\d{4}\.\d{4,5}(v\d+)?$'
    return bool(re.match(pattern, arxiv_id))


def get_paper_id_from_filename(filename: str) -> Optional[str]:
    """
    从文件名中提取 arXiv ID
    
    Args:
        filename: 文件名
        
    Returns:
        arXiv ID 或 None
    """
    # 匹配常见的 ID 格式
    pattern = r'(\d{4}\.\d{4,5}(?:v\d+)?)'
    match = re.search(pattern, filename)
    return match.group(1) if match else None
