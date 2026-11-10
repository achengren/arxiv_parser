"""downloader 模块测试"""

import pytest

from arxiv_parser.downloader import PaperDownloader
from arxiv_parser.models import PaperMetadata, DownloadedPaper


def make_metadata():
    return PaperMetadata(
        arxiv_id="2301.12345",
        title="Test Paper",
        authors=["Alice Smith"],
        abstract="abstract",
        categories=["cs.CL"],
        primary_category="cs.CL",
        published_date="2023-01-01",
        updated_date="2023-01-02",
        pdf_url="https://arxiv.org/pdf/2301.12345",
        entry_id="http://arxiv.org/abs/2301.12345",
    )


def test_download_by_metadata_returns_downloaded_paper(tmp_path, monkeypatch):
    downloader = PaperDownloader(download_dir=str(tmp_path))

    pdf = tmp_path / "test.pdf"
    pdf.write_bytes(b"%PDF-1.4")

    monkeypatch.setattr(downloader, "download", lambda url, filename, download_dir=None: str(pdf))

    result = downloader.download_by_metadata(make_metadata())

    assert isinstance(result, DownloadedPaper)
    assert result.local_pdf_path == str(pdf)
    assert result.file_size == len(b"%PDF-1.4")


def test_download_by_metadata_returns_none_on_failure(tmp_path, monkeypatch):
    downloader = PaperDownloader(download_dir=str(tmp_path))
    monkeypatch.setattr(downloader, "download", lambda url, filename, download_dir=None: None)

    result = downloader.download_by_metadata(make_metadata())
    assert result is None


def test_remote_url_pdf():
    d = PaperDownloader()
    assert d._remote_url("2301.12345v1") == "https://arxiv.org/pdf/2301.12345v1"


def test_remote_url_source():
    d = PaperDownloader(kind="source")
    assert d._remote_url("2301.12345") == "https://arxiv.org/e-print/2301.12345"


def test_invalid_kind_raises():
    with pytest.raises(ValueError):
        PaperDownloader(kind="doc")
