"""pipeline 模块测试（断点续处理 / 缓存复用）"""

from arxiv_parser.config import Config
from arxiv_parser.pipeline import PaperPipeline
from arxiv_parser.models import (
    PaperMetadata, DownloadedPaper, ParsedPaper, AnalyzedPaper
)


def make_metadata():
    return PaperMetadata(
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


def make_parsed():
    metadata = make_metadata()
    downloaded = DownloadedPaper(metadata=metadata, local_pdf_path="/tmp/x.pdf")
    return ParsedPaper(downloaded=downloaded, full_text="text")


def _config(tmp_path):
    config = Config()
    config.paths.db_path = str(tmp_path / "papers.db")
    config.paths.pdf_dir = str(tmp_path / "pdfs")
    config.paths.image_dir = str(tmp_path / "images")
    return config


def test_pipeline_reuses_cache_on_second_run(tmp_path, monkeypatch):
    pipeline = PaperPipeline(config=_config(tmp_path), llm_client=None)

    metadata = make_metadata()
    parsed = make_parsed()

    monkeypatch.setattr(pipeline.fetcher, "search_by_id", lambda arxiv_id: metadata)
    monkeypatch.setattr(
        pipeline.downloader, "download_by_metadata",
        lambda m, download_dir=None: parsed.downloaded,
    )
    monkeypatch.setattr(pipeline.parser, "parse_pdf", lambda d: parsed)

    calls = {"n": 0}

    def fake_analyze(p, analysis_types=None):
        calls["n"] += 1
        return AnalyzedPaper(parsed=p, summary_zh="s", llm_model="mock")

    monkeypatch.setattr(pipeline.analyzer, "analyze", fake_analyze)

    # 第一次：真正分析
    r1 = pipeline.process("2301.12345")
    assert calls["n"] == 1
    assert r1.summary_zh == "s"

    # 第二次：命中缓存，跳过 LLM
    r2 = pipeline.process("2301.12345")
    assert calls["n"] == 1
    assert r2.summary_zh == "s"

    # force=True：强制重新分析
    r3 = pipeline.process("2301.12345", force=True)
    assert calls["n"] == 2
