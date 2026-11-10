"""PDF 解析模块"""

import re
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime

from loguru import logger

try:
    import pymupdf
    FITZ_AVAILABLE = True
except ImportError:
    FITZ_AVAILABLE = False
    logger.warning("PyMuPDF 未安装，PDF 解析功能不可用")

from .models import (
    DownloadedPaper, ParsedPaper, Section, ImageInfo, TableInfo, Reference
)


class ArxivParser:
    """arXiv 论文 PDF 解析器"""
    
    def __init__(self, image_output_dir: str = "output/images"):
        """
        初始化解析器
        
        Args:
            image_output_dir: 图片输出目录
        """
        if not FITZ_AVAILABLE:
            raise RuntimeError("请安装 PyMuPDF: pip install PyMuPDF")
        
        self.image_output_dir = Path(image_output_dir)
        self.image_output_dir.mkdir(parents=True, exist_ok=True)
    
    def parse_pdf(self, downloaded: DownloadedPaper) -> ParsedPaper:
        """
        解析完整论文
        
        Args:
            downloaded: 已下载的论文
        
        Returns:
            解析后的论文
        """
        pdf_path = downloaded.local_pdf_path
        logger.info(f"开始解析 PDF: {pdf_path}")
        
        try:
            doc = pymupdf.open(pdf_path)
            
            # 提取文本
            full_text = self.extract_text(pdf_path)
            
            # 提取章节
            sections = self._extract_sections(doc, full_text)
            
            # 提取图片
            images = self.extract_images(pdf_path, str(self.image_output_dir))
            
            # 提取表格（简化版）
            tables = self._extract_tables(doc)
            
            # 提取参考文献
            references = self._extract_references(full_text)
            
            # 获取页数
            page_count = len(doc)
            
            doc.close()
            
            parsed = ParsedPaper(
                downloaded=downloaded,
                full_text=full_text,
                sections=sections,
                images=images,
                tables=tables,
                references=references,
                page_count=page_count,
                parse_time=datetime.now().isoformat(),
                parse_errors=[]
            )
            
            logger.info(f"解析完成: {page_count} 页, {len(sections)} 章节, {len(images)} 图片")
            return parsed
            
        except Exception as e:
            logger.error(f"解析失败: {e}")
            return ParsedPaper(
                downloaded=downloaded,
                parse_errors=[str(e)]
            )
    
    def extract_text(self, pdf_path: str) -> str:
        """
        提取纯文本
        
        Args:
            pdf_path: PDF 文件路径
        
        Returns:
            提取的文本
        """
        doc = pymupdf.open(pdf_path)
        text_parts = []
        
        for page in doc:
            text_parts.append(page.get_text())
        
        doc.close()
        return "\n".join(text_parts)
    
    def extract_images(self, pdf_path: str, output_dir: str) -> List[ImageInfo]:
        """
        提取图片
        
        Args:
            pdf_path: PDF 文件路径
            output_dir: 输出目录
        
        Returns:
            图片信息列表
        """
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        doc = pymupdf.open(pdf_path)
        images = []
        image_id = 0
        
        # 从文件名提取 arxiv_id
        pdf_name = Path(pdf_path).stem
        
        for page_num, page in enumerate(doc):
            image_list = page.get_images(full=True)
            
            for img_index, img in enumerate(image_list):
                xref = img[0]
                base_image = doc.extract_image(xref)
                
                if base_image:
                    image_bytes = base_image["image"]
                    image_ext = base_image["ext"]
                    
                    # 保存图片
                    image_filename = f"{pdf_name}_page{page_num+1}_img{image_id+1}"
                    image_path = output_path / (image_filename + "." + image_ext)
                    
                    with open(image_path, "wb") as f:
                        f.write(image_bytes)
                    
                    images.append(ImageInfo(
                        image_id=image_id,
                        page_number=page_num + 1,
                        local_path=str(image_path),
                        caption=None,  # 需要 LLM 生成
                        width=base_image.get("width"),
                        height=base_image.get("height")
                    ))
                    
                    image_id += 1
        
        doc.close()
        logger.debug(f"提取了 {len(images)} 张图片")
        return images

    def extract_sections(self, pdf_path: str) -> List[Section]:
        """提取章节结构"""
        doc = pymupdf.open(pdf_path)
        full_text = self.extract_text(pdf_path)
        try:
            return self._extract_sections(doc, full_text)
        finally:
            doc.close()

    def extract_tables(self, pdf_path: str) -> List[TableInfo]:
        """提取表格"""
        doc = pymupdf.open(pdf_path)
        try:
            return self._extract_tables(doc)
        finally:
            doc.close()

    def _extract_sections(self, doc: pymupdf.Document, full_text: str) -> List[Section]:
        """
        提取章节结构（简化版）
        
        使用正则表达式匹配常见的章节标题
        """
        sections = []
        
        # 常见的论文章节模式
        patterns = [
            r'(?m)^(Abstract|摘要)\s*$',
            r'(?m)^(Introduction|引言|1\.\s*Introduction)\s*$',
            r'(?m)^(Related Work|相关工作|2\.\s*Related Work)\s*$',
            r'(?m)^(Method|方法|3\.\s*Method)\s*$',
            r'(?m)^(Experiment|实验|4\.\s*Experiment)\s*$',
            r'(?m)^(Result|结果|5\.\s*Result)\s*$',
            r'(?m)^(Discussion|讨论|6\.\s*Discussion)\s*$',
            r'(?m)^(Conclusion|结论|7\.\s*Conclusion)\s*$',
            r'(?m)^(Reference|参考文献)\s*$',
        ]
        
        # 查找所有章节标题
        section_titles = []
        for pattern in patterns:
            matches = re.finditer(pattern, full_text, re.IGNORECASE)
            for match in matches:
                section_titles.append((match.start(), match.group()))
        
        # 按位置排序
        section_titles.sort(key=lambda x: x[0])
        
        # 提取章节内容
        for i, (start_pos, title) in enumerate(section_titles):
            end_pos = section_titles[i+1][0] if i+1 < len(section_titles) else len(full_text)
            content = full_text[start_pos:end_pos].strip()
            
            sections.append(Section(
                name=title,
                content=content[:2000],  # 限制长度
                level=1,
                start_page=None,
                end_page=None
            ))
        
        logger.debug(f"提取了 {len(sections)} 个章节")
        return sections
    
    def _extract_tables(self, doc: pymupdf.Document) -> List[TableInfo]:
        """
        提取表格（简化版）
        
        实际项目中可以使用 pdfplumber 或专门的表格提取工具
        """
        # 这里只是一个占位实现
        # 完整的表格提取需要更复杂的算法
        return []
    
    def _extract_references(self, full_text: str) -> List[Reference]:
        """
        提取参考文献（简化版）
        
        使用正则表达式匹配常见的引用格式
        """
        references = []
        
        # 找到参考文献部分
        ref_pattern = r'(?m)^References?\s*$'
        ref_match = re.search(ref_pattern, full_text, re.IGNORECASE)
        
        if not ref_match:
            return references
        
        ref_text = full_text[ref_match.end():]
        
        # 匹配常见的引用格式 [1], [2], etc.
        ref_items = re.findall(r'\[(\d+)\]\s*([^\[]+?)(?=\[\d+\]|$)', ref_text, re.DOTALL)
        
        for ref_id, ref_content in ref_items[:20]:  # 限制数量
            references.append(Reference(
                ref_id=ref_id,
                text=ref_content.strip()[:500],  # 限制长度
                url=None,
                doi=None
            ))
        
        logger.debug(f"提取了 {len(references)} 条参考文献")
        return references
