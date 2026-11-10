"""端到端处理流水线

统一编排：获取元数据 → 下载 PDF → 解析 → LLM 分析 → 持久化到数据库。
CLI 和 MCP 都走这里，避免各自重复实现同一套流程。

依赖注入：llm_client 由组装层（CLI / MCP）通过工厂构建后注入，
核心层不依赖任何适配器实现。
"""

from typing import List, Optional

from loguru import logger

from .config import Config
from .llm import LLMAdapter
from .models import AnalyzedPaper, AnalysisType, PaperStatus
from .fetcher import ArxivFetcher
from .downloader import PaperDownloader
from .parser import ArxivParser
from .analyzer import ArxivAnalyzer
from .database import DatabaseManager


class PaperPipeline:
    """论文处理流水线：负责编排和持久化，返回分析结果。"""

    def __init__(
        self,
        config: Optional[Config] = None,
        llm_client: Optional[LLMAdapter] = None,
    ):
        self.config = config or Config.from_yaml()
        paths = self.config.paths

        self.db = DatabaseManager(paths.db_path)
        self.fetcher = ArxivFetcher(config=self.config.arxiv)
        self.downloader = PaperDownloader(download_dir=paths.pdf_dir)
        self.parser = ArxivParser(image_output_dir=paths.image_dir)
        self.analyzer = ArxivAnalyzer(llm_client=llm_client)

    def process(
        self,
        arxiv_id: str,
        analysis_types: Optional[List[AnalysisType]] = None,
        force: bool = False,
    ) -> AnalyzedPaper:
        """处理单篇论文的完整流程。

        Args:
            arxiv_id: arXiv 论文 ID
            analysis_types: 要执行的分析类型，默认 None（分析器用默认集合）
            force: 是否强制重新分析（跳过缓存）

        Returns:
            AnalyzedPaper（含 parsed.downloaded.metadata）

        Raises:
            ValueError: 论文不存在
            RuntimeError: 下载/解析/分析失败
        """
        # 1. 获取元数据
        metadata = self.fetcher.search_by_id(arxiv_id)
        if not metadata:
            raise ValueError(f"未找到论文: {arxiv_id}")

        # 统一使用 metadata 中的 arxiv_id（含版本号），保证数据库状态更新能定位到行
        arxiv_id = metadata.arxiv_id
        self.db.save_paper_metadata(metadata)
        logger.info("✓ 保存论文元数据到数据库")

        # 2. 下载 PDF
        downloaded = self.downloader.download_by_metadata(metadata)
        if not downloaded:
            raise RuntimeError(f"下载论文失败: {arxiv_id}")

        self.db.update_paper_status(arxiv_id, 'download_status', PaperStatus.COMPLETED.value)
        logger.info("✓ 更新下载状态")

        # 3. 解析 PDF
        parsed = self.parser.parse_pdf(downloaded)
        if parsed.parse_errors:
            raise RuntimeError(f"解析论文失败: {parsed.parse_errors}")

        self.db.save_parsed_paper(parsed)
        logger.info("✓ 保存解析结果到数据库")

        # 4. LLM 分析（断点续处理：默认分析类型且已有结果时复用缓存，跳过 LLM 调用）
        use_cache = (analysis_types is None) and (not force)
        cached = self.db.get_analysis_result(arxiv_id) if use_cache else None

        if cached is not None:
            analyzed = self._from_cached(parsed, cached)
            logger.info("✓ 命中缓存，跳过 LLM 分析")
        else:
            analyzed = self.analyzer.analyze(parsed, analysis_types=analysis_types)
            if analyzed.analysis_errors:
                raise RuntimeError(f"分析论文失败: {analyzed.analysis_errors}")

            self.db.update_paper_status(arxiv_id, 'analyze_status', PaperStatus.COMPLETED.value)
            self.db.save_analysis_result(arxiv_id, analyzed)
            logger.info("✓ 保存分析结果到数据库")

        logger.success(f"✓ 论文处理完成: {arxiv_id}")
        return analyzed

    @staticmethod
    def _from_cached(parsed, cached) -> AnalyzedPaper:
        """从缓存的 AnalysisResult 重建 AnalyzedPaper（跳过 LLM 调用）"""
        return AnalyzedPaper(
            parsed=parsed,
            summary_zh=cached.summary_zh,
            summary_en=cached.summary_en,
            innovations=cached.innovations,
            methodology=cached.methodology,
            experiments=cached.experiments,
            conclusions=cached.conclusions,
            novelty_score=cached.novelty_score,
            quality_score=cached.quality_score,
            qa_pairs=cached.qa_pairs,
            keywords=cached.keywords,
            analysis_time=cached.analysis_time,
            llm_model=cached.llm_model,
            analysis_errors=[],
        )
