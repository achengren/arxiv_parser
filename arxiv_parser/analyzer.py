"""LLM 分析模块"""

import json
from typing import List, Optional
from datetime import datetime

from loguru import logger

from .llm import LLMAdapter
from .models import ParsedPaper, AnalyzedPaper, QAPair, AnalysisType


class ArxivAnalyzer:
    """arXiv 论文 LLM 分析器（依赖注入 LLM 客户端）"""

    DEFAULT_ANALYSIS_TYPES = [
        AnalysisType.SUMMARY,
        AnalysisType.INNOVATION,
        AnalysisType.KEYWORDS,
        AnalysisType.QA_GENERATION,
    ]

    def __init__(self, llm_client: Optional[LLMAdapter] = None):
        """
        初始化分析器

        Args:
            llm_client: LLM 客户端（LLMAdapter 实例），None 时使用 mock 模式
        """
        self.llm_client = llm_client

    @property
    def use_mock(self) -> bool:
        """是否处于 mock 模式（未注入 LLM 客户端）"""
        return self.llm_client is None

    def analyze(
        self,
        parsed: ParsedPaper,
        analysis_types: Optional[List[AnalysisType]] = None
    ) -> AnalyzedPaper:
        """
        完整分析流程

        Args:
            parsed: 解析后的论文
            analysis_types: 要执行的分析类型列表

        Returns:
            分析后的论文
        """
        if analysis_types is None:
            analysis_types = self.DEFAULT_ANALYSIS_TYPES

        logger.info(f"开始分析论文: {parsed.downloaded.metadata.arxiv_id}")

        text = parsed.full_text

        # 执行各项分析
        summary_zh = ""
        summary_en = ""
        innovations = []
        methodology = ""
        experiments = ""
        conclusions = ""
        qa_pairs = []
        keywords = []
        novelty_score = None
        quality_score = None

        try:
            if AnalysisType.SUMMARY in analysis_types:
                summary_zh = self.generate_summary(text, language="zh")
                summary_en = self.generate_summary(text, language="en")
                logger.debug("✓ 生成摘要完成")

            if AnalysisType.INNOVATION in analysis_types:
                innovations = self.extract_innovations(text)
                logger.debug(f"✓ 提取创新点: {len(innovations)} 个")

            if AnalysisType.METHODOLOGY in analysis_types:
                methodology = self.extract_methodology(text)
                logger.debug("✓ 提取方法完成")

            if AnalysisType.EXPERIMENTS in analysis_types:
                experiments = self._extract_experiments(text)
                logger.debug("✓ 提取实验完成")

            if AnalysisType.QA_GENERATION in analysis_types:
                qa_pairs = self.generate_qa_pairs(text, num_pairs=5)
                logger.debug(f"✓ 生成问答对: {len(qa_pairs)} 个")

            if AnalysisType.CONCLUSIONS in analysis_types:
                conclusions = self._extract_conclusions(text)
                logger.debug("✓ 提取结论完成")

            if AnalysisType.KEYWORDS in analysis_types:
                keywords = self._extract_keywords(text)
                logger.debug(f"✓ 提取关键词: {len(keywords)} 个")

            if AnalysisType.NOVELTY_SCORING in analysis_types:
                novelty_score = self.score_novelty(text)
                logger.debug(f"✓ 新颖性评分: {novelty_score}")

        except Exception as e:
            logger.error(f"分析过程中出错: {e}")
            import traceback
            traceback.print_exc()
            return AnalyzedPaper(
                parsed=parsed,
                analysis_errors=[str(e)]
            )

        analyzed = AnalyzedPaper(
            parsed=parsed,
            summary_zh=summary_zh,
            summary_en=summary_en,
            innovations=innovations,
            methodology=methodology,
            experiments=experiments,
            conclusions=conclusions,
            novelty_score=novelty_score,
            quality_score=quality_score,
            qa_pairs=qa_pairs,
            keywords=keywords,
            analysis_time=datetime.now().isoformat(),
            llm_model=self.llm_client.model if self.llm_client else 'mock',
            analysis_errors=[]
        )

        logger.success(f"✓ 论文分析完成: {parsed.downloaded.metadata.arxiv_id}")
        return analyzed

    def generate_summary(self, text: str, language: str = "zh") -> str:
        """
        生成摘要

        Args:
            text: 论文全文
            language: 摘要语言（zh/en）

        Returns:
            摘要文本
        """
        if self.use_mock:
            # 模拟模式：返回前 500 字符
            return text[:500] + "..." if len(text) > 500 else text

        lang_name = "中文" if language == "zh" else "English"
        prompt = f"""请为以下学术论文生成一个简洁的{lang_name}摘要（200-300字），概括研究问题、方法和主要贡献。

论文内容：
{text[:3000]}

请直接用{lang_name}输出摘要，不要添加额外说明。"""

        try:
            response = self.llm_client.complete(
                prompt=prompt,
                system_prompt="你是一位专业的学术论文分析助手，擅长提取论文的核心信息。"
            )
            return response.content
        except Exception as e:
            logger.error(f"生成摘要失败: {e}")
            return ""

    def extract_innovations(self, text: str) -> List[str]:
        """
        提取创新点

        Args:
            text: 论文全文

        Returns:
            创新点列表
        """
        if self.use_mock:
            # 模拟模式
            return [
                "提出了一种新的方法",
                "在某个数据集上取得了最优结果",
                "解决了某个具体问题"
            ]

        prompt = f"""请提取以下学术论文的主要创新点（3-5个），以列表形式返回。

论文内容：
{text[:3000]}

请按以下格式输出：
1. 创新点一
2. 创新点二
..."""

        try:
            response = self.llm_client.complete(
                prompt=prompt,
                system_prompt="你是一位专业的学术论文分析助手，擅长识别研究创新点。"
            )
            # 解析列表
            lines = response.content.strip().split('\n')
            innovations = []
            for line in lines:
                line = line.strip()
                if line and (line[0].isdigit() or line.startswith('-')):
                    # 移除序号和前缀
                    innovation = line.lstrip('0123456789.-) ')
                    if innovation:
                        innovations.append(innovation)

            return innovations if innovations else [response.content]
        except Exception as e:
            logger.error(f"提取创新点失败: {e}")
            return []

    def generate_qa_pairs(self, text: str, num_pairs: int = 5) -> List[QAPair]:
        """
        生成问答对

        Args:
            text: 论文全文
            num_pairs: 问答对数量

        Returns:
            问答对列表
        """
        if self.use_mock:
            # 模拟模式
            return [
                QAPair(
                    question="这篇论文的主要贡献是什么？",
                    answer="提出了一个新的方法。",
                    qa_type="understanding"
                ),
                QAPair(
                    question="这个方法与现有方法有什么区别？",
                    answer="性能更好。",
                    qa_type="comparison"
                )
            ]

        prompt = f"""请根据这篇学术论文生成 {num_pairs} 个问答对，帮助读者理解论文内容。
以 JSON 格式返回，每个问答对包含 question 和 answer 字段。

论文内容：
{text[:2000]}

请返回 JSON 数组格式：
[
  {{"question": "...", "answer": "..."}},
  ...
]"""

        try:
            response = self.llm_client.complete(
                prompt=prompt,
                system_prompt="你是一位专业的学术论文分析助手，擅长生成帮助理解论文的问答对。"
            )
            # 尝试解析 JSON
            content = response.content.strip()
            # 查找 JSON 数组
            if '[' in content and ']' in content:
                start = content.find('[')
                end = content.rfind(']') + 1
                json_str = content[start:end]
                qa_data = json.loads(json_str)
                return [
                    QAPair(
                        question=qa['question'],
                        answer=qa['answer'],
                        qa_type='general'
                    )
                    for qa in qa_data
                ]
            else:
                logger.warning("无法解析 JSON，返回原始内容")
                return [QAPair(question="论文内容", answer=content, qa_type='general')]
        except Exception as e:
            logger.error(f"生成问答对失败: {e}")
            return []

    def extract_methodology(self, text: str) -> str:
        """提取方法论"""
        if self.use_mock:
            return "该方法基于深度学习技术。"

        prompt = f"""请简要描述这篇论文的核心方法论（300字以内），包括使用的技术、算法或框架。

论文内容：
{text[:2000]}"""

        try:
            response = self.llm_client.complete(
                prompt=prompt,
                system_prompt="你是一位专业的学术论文分析助手，擅长提取研究方法。"
            )
            return response.content
        except Exception as e:
            logger.error(f"提取方法论失败: {e}")
            return ""

    def _extract_experiments(self, text: str) -> str:
        """提取实验信息"""
        if self.use_mock:
            return "在标准数据集上进行了实验验证。"

        prompt = f"""请简要描述这篇论文的实验设置和主要结果（300字以内）。

论文内容：
{text[:2000]}"""

        try:
            response = self.llm_client.complete(
                prompt=prompt,
                system_prompt="你是一位专业的学术论文分析助手，擅长提取实验信息。"
            )
            return response.content
        except Exception as e:
            logger.error(f"提取实验信息失败: {e}")
            return ""

    def _extract_keywords(self, text: str) -> List[str]:
        """提取关键词"""
        if self.use_mock:
            return ["deep learning", "neural network", "NLP"]

        prompt = f"""请提取这篇论文的 5-10 个关键词，以逗号分隔。

论文内容：
{text[:1000]}"""

        try:
            response = self.llm_client.complete(
                prompt=prompt,
                system_prompt="你是一位专业的学术论文分析助手，擅长提取关键词。"
            )
            keywords = [kw.strip() for kw in response.content.split(',')]
            return keywords[:10]
        except Exception as e:
            logger.error(f"提取关键词失败: {e}")
            return []

    def _extract_conclusions(self, text: str) -> str:
        """提取结论"""
        if self.use_mock:
            return "总结了论文的主要发现和贡献。"

        prompt = f"""请简要总结这篇论文的主要结论（300字以内）。

论文内容：
{text[:2000]}"""

        try:
            response = self.llm_client.complete(
                prompt=prompt,
                system_prompt="你是一位专业的学术论文分析助手，擅长总结研究结论。"
            )
            return response.content
        except Exception as e:
            logger.error(f"提取结论失败: {e}")
            return ""

    def score_novelty(self, text: str) -> int:
        """评分新颖性（1-5）"""
        if self.use_mock:
            return 3

        prompt = f"""请评估以下学术论文的创新性，给出 1-5 分（只输出一个整数）。

论文内容：
{text[:1500]}"""

        try:
            response = self.llm_client.complete(
                prompt=prompt,
                system_prompt="你是一位专业的学术论文评审助手。"
            )
            score = int(response.content.strip())
            return max(1, min(5, score))
        except Exception as e:
            logger.error(f"评分新颖性失败: {e}")
            return 3
