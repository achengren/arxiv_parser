"""database 模块测试（SQLite 临时库）"""

from arxiv_parser.database import DatabaseManager
from arxiv_parser.models import (
    PaperMetadata, DownloadedPaper, ParsedPaper
)


def make_metadata(arxiv_id="2301.12345"):
    return PaperMetadata(
        arxiv_id=arxiv_id,
        title="Test",
        authors=["Alice", "Bob"],
        abstract="abstract",
        categories=["cs.CL"],
        primary_category="cs.CL",
        published_date="2023-01-01",
        updated_date="2023-01-02",
        pdf_url="http://x",
        entry_id="http://x",
    )


def make_parsed(metadata):
    downloaded = DownloadedPaper(metadata=metadata, local_pdf_path="/tmp/x.pdf")
    return ParsedPaper(downloaded=downloaded, full_text="hello world full text", page_count=1)


def test_save_and_get_metadata(tmp_path):
    db = DatabaseManager(str(tmp_path / "test.db"))
    db.save_paper_metadata(make_metadata())

    meta = db.get_paper_metadata("2301.12345")
    assert meta.title == "Test"
    assert meta.authors == ["Alice", "Bob"]


def test_get_full_text_versionless_match(tmp_path):
    db = DatabaseManager(str(tmp_path / "test.db"))
    metadata = make_metadata("1706.03762v7")
    db.save_paper_metadata(metadata)
    db.save_parsed_paper(make_parsed(metadata))

    assert db.get_full_text("1706.03762") == "hello world full text"


def test_get_paper_status_defaults_to_pending(tmp_path):
    db = DatabaseManager(str(tmp_path / "test.db"))
    db.save_paper_metadata(make_metadata())

    assert db.get_paper_status("2301.12345") == {
        "download_status": "pending",
        "parse_status": "pending",
        "analyze_status": "pending",
    }


def test_get_paper_status_unknown_id(tmp_path):
    db = DatabaseManager(str(tmp_path / "test.db"))
    assert db.get_paper_status("9999.99999") == {}
