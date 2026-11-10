"""analyzer 模块测试（mock 模式，验证 AnalysisType 枚举接线）"""

from arxiv_parser.analyzer import ArxivAnalyzer
from arxiv_parser.models import (
    PaperMetadata, DownloadedPaper, ParsedPaper, AnalysisType
)


def make_parsed():
    metadata = PaperMetadata(
        arxiv_id="2301.12345",
        title="Test",
        authors=["A"],
        abstract="",
        categories=["cs.CL"],
        primary_category="cs.CL",
        published_date="2023-01-01",
        updated_date="2023-01-02",
        pdf_url="http://x",
        entry_id="http://x",
    )
    downloaded = DownloadedPaper(metadata=metadata, local_pdf_path="/tmp/x.pdf")
    return ParsedPaper(downloaded=downloaded, full_text="some paper text " * 100)


def test_mock_default_types_populate():
    analyzer = ArxivAnalyzer()
    result = analyzer.analyze(make_parsed())

    assert result.llm_model == "mock"
    assert result.summary_zh
    assert result.innovations
    assert result.keywords
    assert result.qa_pairs


def test_conclusions_not_in_default():
    analyzer = ArxivAnalyzer()
    result = analyzer.analyze(make_parsed())
    assert result.conclusions == ""


def test_conclusions_when_requested():
    analyzer = ArxivAnalyzer()
    result = analyzer.analyze(make_parsed(), analysis_types=[AnalysisType.CONCLUSIONS])
    assert result.conclusions != ""


def test_novelty_scoring_when_requested():
    analyzer = ArxivAnalyzer()
    result = analyzer.analyze(make_parsed(), analysis_types=[AnalysisType.NOVELTY_SCORING])
    assert result.novelty_score is not None


def test_keywords_not_extracted_unless_requested():
    analyzer = ArxivAnalyzer()
    result = analyzer.analyze(make_parsed(), analysis_types=[AnalysisType.SUMMARY])
    assert result.summary_zh != ""
    assert result.keywords == []
