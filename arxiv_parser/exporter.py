"""数据导出模块"""

import json
from pathlib import Path
from typing import Optional, Dict, Any
from datetime import datetime

from loguru import logger

from .models import AnalyzedPaper, OutputData


class ArxivExporter:
    """arXiv 论文数据导出器"""
    
    def __init__(self, output_dir: str = "output/results"):
        """
        初始化导出器

        Args:
            output_dir: 输出目录
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    def export(
        self,
        analyzed: AnalyzedPaper,
        output_format: str = "json",
        output_path: Optional[str] = None
    ) -> OutputData:
        """
        导出数据
        
        Args:
            analyzed: 分析后的论文
            output_format: 输出格式（json/markdown）
            output_path: 输出路径（可选）
        
        Returns:
            输出数据对象
        """
        logger.info(f"导出数据: {analyzed.parsed.downloaded.metadata.arxiv_id}")
        
        # 构建输出数据
        output_data = self._build_output_data(analyzed)
        
        # 保存到文件
        if output_format == "json":
            filepath = self._save_json(output_data, output_path)
        elif output_format == "markdown":
            filepath = self._save_markdown(output_data, output_path)
        else:
            raise ValueError(f"不支持的输出格式: {output_format}")
        
        logger.info(f"导出完成: {filepath}")
        return output_data
    
    def to_json(self, analyzed: AnalyzedPaper) -> str:
        """
        转换为 JSON 字符串
        
        Args:
            analyzed: 分析后的论文
        
        Returns:
            JSON 字符串
        """
        output_data = self._build_output_data(analyzed)
        return output_data.to_json()
    
    def to_markdown(self, analyzed: AnalyzedPaper) -> str:
        """
        转换为 Markdown 字符串
        
        Args:
            analyzed: 分析后的论文
        
        Returns:
            Markdown 字符串
        """
        output_data = self._build_output_data(analyzed)
        return self._format_markdown(output_data)
    
    def _build_output_data(self, analyzed: AnalyzedPaper) -> OutputData:
        """构建输出数据对象"""
        metadata = analyzed.parsed.downloaded.metadata
        
        # 结构化知识（统一英文键，中文展示在 markdown 层映射）
        structured_knowledge = {
            "authors": metadata.authors,
            "published_date": metadata.published_date,
            "methodology": analyzed.methodology,
            "contributions": analyzed.innovations,
            "keywords": analyzed.keywords
        }
        
        # 段落内容
        sections = {}
        for section in analyzed.parsed.sections:
            sections[section.name] = {
                "content": section.content[:500],  # 限制长度
                "level": section.level
            }
        
        # 图片信息
        images = []
        for img in analyzed.parsed.images:
            images.append({
                "image_id": img.image_id,
                "page_number": img.page_number,
                "local_path": img.local_path,
                "caption": img.caption or ""
            })
        
        # 表格信息
        tables = []
        for tbl in analyzed.parsed.tables:
            tables.append({
                "table_id": tbl.table_id,
                "page_number": tbl.page_number,
                "caption": tbl.caption or "",
                "markdown": tbl.markdown or ""
            })
        
        # 参考文献
        references = {
            "count": len(analyzed.parsed.references),
            "items": [
                {
                    "ref_id": ref.ref_id,
                    "text": ref.text[:200]  # 限制长度
                }
                for ref in analyzed.parsed.references[:10]  # 只取前 10 条
            ]
        }
        
        # LLM 分析结果
        analysis = {
            "summary_zh": analyzed.summary_zh,
            "summary_en": analyzed.summary_en,
            "innovations": analyzed.innovations,
            "methodology": analyzed.methodology,
            "experiments": analyzed.experiments,
            "conclusions": analyzed.conclusions,
            "novelty_score": analyzed.novelty_score,
            "quality_score": analyzed.quality_score,
            "qa_pairs": [
                {
                    "question": qa.question,
                    "answer": qa.answer,
                    "qa_type": qa.qa_type
                }
                for qa in analyzed.qa_pairs
            ],
            "llm_model": analyzed.llm_model,
            "analysis_time": analyzed.analysis_time
        }
        
        return OutputData(
            title=metadata.title,
            arxiv_id=metadata.arxiv_id,
            categories=metadata.categories,
            source_url=metadata.pdf_url,
            pdf_path=analyzed.parsed.downloaded.local_pdf_path,
            full_text=analyzed.parsed.full_text,
            structured_knowledge=structured_knowledge,
            sections=sections,
            images=images,
            tables=tables,
            references=references,
            analysis=analysis,
            process_time=datetime.now().isoformat(),
            version="1.0"
        )
    
    def _save_json(self, output_data: OutputData, output_path: Optional[str] = None) -> str:
        """保存为 JSON 文件"""
        if output_path is None:
            filename = f"{output_data.arxiv_id}.json"
            filepath = self.output_dir / filename
        else:
            filepath = Path(output_path)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(output_data.to_json())
        
        return str(filepath)
    
    def _save_markdown(self, output_data: OutputData, output_path: Optional[str] = None) -> str:
        """保存为 Markdown 文件"""
        if output_path is None:
            filename = f"{output_data.arxiv_id}.md"
            filepath = self.output_dir / filename
        else:
            filepath = Path(output_path)
            if filepath.suffix != '.md':
                filepath = filepath.with_suffix('.md')
        
        markdown_content = self._format_markdown(output_data)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(markdown_content)
        
        return str(filepath)
    
    def _format_markdown(self, output_data: OutputData) -> str:
        """格式化为 Markdown"""
        lines = []
        
        # 标题
        lines.append(f"# {output_data.title}\n")
        lines.append(f"**arXiv ID**: {output_data.arxiv_id}\n")
        lines.append(f"**分类**: {', '.join(output_data.categories)}\n")
        lines.append(f"**来源**: [{output_data.source_url}]({output_data.source_url})\n")
        lines.append("---\n")
        
        # 结构化知识
        lines.append("## 基本信息\n")
        knowledge_labels = {
            "authors": "作者",
            "published_date": "发表日期",
            "methodology": "核心方法",
            "contributions": "主要贡献",
            "keywords": "关键词",
        }
        for key, value in output_data.structured_knowledge.items():
            label = knowledge_labels.get(key, key)
            if isinstance(value, list):
                lines.append(f"- **{label}**: {', '.join(str(v) for v in value)}")
            else:
                lines.append(f"- **{label}**: {value}")
        lines.append("")
        
        # 摘要
        if output_data.analysis.get('summary_zh'):
            lines.append("## 中文摘要\n")
            lines.append(output_data.analysis['summary_zh'])
            lines.append("")
        
        if output_data.analysis.get('summary_en'):
            lines.append("## English Abstract\n")
            lines.append(output_data.analysis['summary_en'])
            lines.append("")
        
        # 创新点
        if output_data.analysis.get('innovations'):
            lines.append("## 主要创新点\n")
            for i, innovation in enumerate(output_data.analysis['innovations'], 1):
                lines.append(f"{i}. {innovation}")
            lines.append("")
        
        # 方法论
        if output_data.analysis.get('methodology'):
            lines.append("## 核心方法\n")
            lines.append(output_data.analysis['methodology'])
            lines.append("")
        
        # 问答对
        if output_data.analysis.get('qa_pairs'):
            lines.append("## 问答\n")
            for i, qa in enumerate(output_data.analysis['qa_pairs'], 1):
                lines.append(f"### Q{i}: {qa['question']}\n")
                lines.append(f"**A**: {qa['answer']}\n")
            lines.append("")
        
        # 图片
        if output_data.images:
            lines.append("## 图片\n")
            for img in output_data.images:
                lines.append(f"- 图片 {img['image_id']} (第 {img['page_number']} 页): `{img['local_path']}`")
            lines.append("")
        
        # 参考文献
        if output_data.references.get('items'):
            lines.append(f"## 参考文献（共 {output_data.references['count']} 条）\n")
            for ref in output_data.references['items'][:5]:
                lines.append(f"[{ref['ref_id']}] {ref['text']}")
            if output_data.references['count'] > 5:
                lines.append(f"... 还有 {output_data.references['count'] - 5} 条")
            lines.append("")
        
        # 元信息
        lines.append("---\n")
        lines.append(f"*生成时间: {output_data.process_time}*  \n")
        lines.append(f"*版本: {output_data.version}*  \n")
        lines.append(f"*LLM 模型: {output_data.analysis.get('llm_model', 'N/A')}*\n")
        
        return '\n'.join(lines)
