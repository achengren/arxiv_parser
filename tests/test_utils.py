"""utils 模块的纯函数测试"""

from arxiv_parser.utils import (
    parse_arxiv_id,
    normalize_arxiv_id,
    generate_filename,
    is_valid_arxiv_id,
    get_paper_id_from_filename,
)


def test_parse_arxiv_id_pure():
    assert parse_arxiv_id("2301.12345") == "2301.12345"


def test_parse_arxiv_id_with_version():
    assert parse_arxiv_id("2301.12345v3") == "2301.12345"


def test_parse_arxiv_id_from_abs_url():
    assert parse_arxiv_id("https://arxiv.org/abs/2301.12345") == "2301.12345"


def test_parse_arxiv_id_from_pdf_url():
    assert parse_arxiv_id("https://arxiv.org/pdf/2301.12345v2.pdf") == "2301.12345"


def test_parse_arxiv_id_invalid():
    assert parse_arxiv_id("not-an-id") is None
    assert parse_arxiv_id("") is None


def test_is_valid_arxiv_id():
    assert is_valid_arxiv_id("2301.12345") is True
    assert is_valid_arxiv_id("2301.12345v1") is True
    assert is_valid_arxiv_id("nonsense") is False


def test_generate_filename():
    name = generate_filename("2301.12345", author="Smith", year="2023")
    assert name == "2023_Smith_2301.12345.pdf"


def test_normalize_arxiv_id():
    assert normalize_arxiv_id("2301.12345v2") == "2301.12345v2"


def test_get_paper_id_from_filename():
    assert get_paper_id_from_filename("2023_Smith_2301.12345.pdf") == "2301.12345"
