"""exporter 模块测试（覆盖 markdown 导出 bug 修复）"""

from arxiv_parser.models import (
    PaperMetadata,
    DownloadedPaper,
    ParsedPaper,
    AnalyzedPaper,
)
from arxiv_parser.exporter import ArxivExporter


def make_analyzed():
    metadata = PaperMetadata(
        arxiv_id="2301.12345",
        title="Test Paper",
        authors=["Alice", "Bob"],
        abstract="abstract",
        categories=["cs.CL"],
        primary_category="cs.CL",
        published_date="2023-01-01",
        updated_date="2023-01-02",
        pdf_url="http://example.com/pdf",
        entry_id="http://arxiv.org/abs/2301.12345",
    )
    downloaded = DownloadedPaper(metadata=metadata, local_pdf_path="/tmp/test.pdf")
    parsed = ParsedPaper(downloaded=downloaded, full_text="hello world")
    analyzed = AnalyzedPaper(
        parsed=parsed,
        summary_zh="中文摘要",
        innovations=["创新点一"],
        keywords=["kw"],
    )
    return analyzed


def test_export_markdown_writes_file(tmp_path):
    exporter = ArxivExporter(output_dir=str(tmp_path))
    analyzed = make_analyzed()

    out_path = tmp_path / "out.md"
    exporter.export(analyzed, "markdown", output_path=str(out_path))

    assert out_path.exists()
    content = out_path.read_text(encoding="utf-8")
    assert "Test Paper" in content
    assert "中文摘要" in content


def test_export_json_writes_file(tmp_path):
    exporter = ArxivExporter(output_dir=str(tmp_path))
    analyzed = make_analyzed()

    out_path = tmp_path / "out.json"
    exporter.export(analyzed, "json", output_path=str(out_path))

    assert out_path.exists()
    content = out_path.read_text(encoding="utf-8")
    assert "Test Paper" in content


def test_to_markdown_returns_string():
    exporter = ArxivExporter(output_dir="/tmp")
    analyzed = make_analyzed()
    md = exporter.to_markdown(analyzed)
    assert "Test Paper" in md
