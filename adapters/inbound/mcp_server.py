"""
MCP (Model Context Protocol) Server — 基于官方 mcp SDK (v2)

将本系统暴露为 MCP 工具供 AI 助手调用。
本模块是组装层（composition root）：从 Config 构建依赖并注入，
保证 MCP 与 CLI 走同一套配置与流水线。
"""

import json
from typing import List, Optional

from loguru import logger
from mcp.server.mcpserver import MCPServer

from arxiv_parser import PaperDownloader, ArxivFetcher, DatabaseManager, PaperPipeline
from arxiv_parser.config import Config
from arxiv_parser.models import AnalysisType
from adapters.outbound import build_llm_client

mcp = MCPServer("arxiv-parser")


@mcp.tool()
def download_paper(arxiv_id: str) -> str:
    """从 arXiv 下载论文 PDF"""
    try:
        config = Config.from_yaml()
        downloader = PaperDownloader(download_dir=config.paths.pdf_dir)
        filepath = downloader.download_by_id(arxiv_id)
        if filepath:
            return json.dumps({"success": True, "message": f"论文已下载: {filepath}"}, ensure_ascii=False)
        return json.dumps({"success": False, "message": f"下载失败: {arxiv_id}"}, ensure_ascii=False)
    except Exception as e:
        return json.dumps({"success": False, "message": str(e)}, ensure_ascii=False)


@mcp.tool()
def get_paper_info(arxiv_id: str) -> str:
    """获取 arXiv 论文的元信息（标题、作者、摘要等）"""
    try:
        config = Config.from_yaml()
        fetcher = ArxivFetcher(config=config.arxiv)
        paper = fetcher.search_by_id(arxiv_id)
        if paper:
            return json.dumps({
                "success": True,
                "data": {
                    "title": paper.title,
                    "authors": paper.authors,
                    "abstract": paper.abstract,
                    "published_date": paper.published_date,
                    "categories": paper.categories,
                    "pdf_url": paper.pdf_url
                }
            }, ensure_ascii=False)
        return json.dumps({"success": False, "message": f"未找到论文: {arxiv_id}"}, ensure_ascii=False)
    except Exception as e:
        return json.dumps({"success": False, "message": str(e)}, ensure_ascii=False)


@mcp.tool()
def search_papers(query: str, max_results: int = 10) -> str:
    """在 arXiv 上搜索论文"""
    try:
        config = Config.from_yaml()
        fetcher = ArxivFetcher(config=config.arxiv)
        papers = fetcher.search_by_query(query, max_results=max_results)
        return json.dumps({
            "success": True,
            "count": len(papers),
            "data": [
                {
                    "arxiv_id": p.arxiv_id,
                    "title": p.title,
                    "authors": p.authors[:3],
                    "published_date": p.published_date
                }
                for p in papers
            ]
        }, ensure_ascii=False)
    except Exception as e:
        return json.dumps({"success": False, "message": str(e)}, ensure_ascii=False)


@mcp.tool()
def analyze_paper(arxiv_id: str, analysis_types: Optional[List[str]] = None) -> str:
    """使用 LLM 分析论文内容，生成摘要、提取创新点和关键词"""
    try:
        config = Config.from_yaml()

        type_enums = None
        if analysis_types is not None:
            type_mapping = {
                "summary": AnalysisType.SUMMARY,
                "innovations": AnalysisType.INNOVATION,
                "keywords": AnalysisType.KEYWORDS,
                "qa_pairs": AnalysisType.QA_GENERATION,
                "methodology": AnalysisType.METHODOLOGY,
                "experiments": AnalysisType.EXPERIMENTS,
                "conclusions": AnalysisType.CONCLUSIONS,
                "novelty": AnalysisType.NOVELTY_SCORING,
            }
            type_enums = [type_mapping[t] for t in analysis_types if t in type_mapping]

        logger.info(f"开始分析论文: {arxiv_id}")
        pipeline = PaperPipeline(config=config, llm_client=build_llm_client(config))
        analyzed = pipeline.process(arxiv_id, analysis_types=type_enums)

        metadata = analyzed.parsed.downloaded.metadata
        result = {
            "success": True,
            "arxiv_id": metadata.arxiv_id,
            "title": metadata.title,
            "authors": metadata.authors[:5],
            "summary_zh": analyzed.summary_zh,
            "summary_en": analyzed.summary_en,
            "innovations": analyzed.innovations,
            "keywords": analyzed.keywords,
            "methodology": analyzed.methodology,
            "experiments": analyzed.experiments,
            "conclusions": analyzed.conclusions,
            "qa_pairs": [
                {"question": qa.question, "answer": qa.answer}
                for qa in analyzed.qa_pairs[:3]
            ] if analyzed.qa_pairs else [],
            "analysis_time": analyzed.analysis_time,
            "llm_model": analyzed.llm_model
        }

        result = {k: v for k, v in result.items() if v}

        return json.dumps(result, ensure_ascii=False)

    except Exception as e:
        logger.error(f"分析论文失败: {e}")
        import traceback
        traceback.print_exc()
        return json.dumps({"success": False, "message": f"分析失败: {str(e)}"}, ensure_ascii=False)


@mcp.tool()
def get_full_text(arxiv_id: str) -> str:
    """获取论文全文（需先运行 analyze_paper 解析入库）"""
    try:
        config = Config.from_yaml()
        db = DatabaseManager(config.paths.db_path)
        full_text = db.get_full_text(arxiv_id)
        if full_text:
            return json.dumps({
                "success": True,
                "arxiv_id": arxiv_id,
                "length": len(full_text),
                "full_text": full_text
            }, ensure_ascii=False)
        return json.dumps({
            "success": False,
            "message": f"未找到论文全文（可能尚未解析入库）: {arxiv_id}"
        }, ensure_ascii=False)
    except Exception as e:
        return json.dumps({"success": False, "message": str(e)}, ensure_ascii=False)


def main():
    """启动 MCP Server（stdio 传输）"""
    mcp.run()


if __name__ == "__main__":
    main()
