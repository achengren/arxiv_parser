"""下载模块

只负责把 URL 下载到本地，不涉及任何检索逻辑（检索归 fetcher）。
"""

import requests
from pathlib import Path
from typing import Optional

from loguru import logger

from .models import DownloadedPaper
from .utils import normalize_arxiv_id, generate_filename


class PaperDownloader:
    """论文下载器（PDF 或 LaTeX 源文件）"""

    def __init__(self, download_dir: str = "output/pdfs", kind: str = "pdf"):
        """
        初始化下载器

        Args:
            download_dir: 保存目录
            kind: 下载类型，'pdf' 或 'source'
        """
        if kind not in ("pdf", "source"):
            raise ValueError(f"不支持的下载类型: {kind}（可选 pdf / source）")

        self.kind = kind
        self.extension = ".pdf" if kind == "pdf" else ".tar.gz"
        self.download_dir = Path(download_dir)
        self.download_dir.mkdir(parents=True, exist_ok=True)
        logger.info(f"PaperDownloader initialized: kind={kind}, dir={self.download_dir}")

    def _remote_url(self, arxiv_id: str) -> str:
        """根据下载类型返回 PDF 或源文件 URL"""
        if self.kind == "pdf":
            return f"https://arxiv.org/pdf/{arxiv_id}"
        return f"https://arxiv.org/e-print/{arxiv_id}"

    def download(
        self,
        url: str,
        filename: str,
        download_dir: Optional[str] = None,
    ) -> Optional[str]:
        """
        下载一个 URL 到本地文件，已存在则直接返回路径。

        Returns:
            下载成功返回文件路径，失败返回 None
        """
        directory = Path(download_dir) if download_dir else self.download_dir
        directory.mkdir(parents=True, exist_ok=True)
        filepath = directory / filename

        if filepath.exists():
            logger.info(f"Already exists: {filepath}")
            return str(filepath)

        try:
            response = requests.get(url, timeout=60, stream=True)
            response.raise_for_status()

            with open(filepath, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)

            logger.success(f"Downloaded: {filepath}")
            return str(filepath)

        except requests.exceptions.RequestException as e:
            logger.error(f"Network error downloading {url}: {e}")
            return None
        except Exception as e:
            logger.error(f"Error downloading {url}: {e}")
            return None

    def download_by_id(
        self,
        arxiv_id: str,
        filename: Optional[str] = None,
        download_dir: Optional[str] = None,
    ) -> Optional[str]:
        """
        通过 arXiv ID 下载（直接构造 URL，不查询 API）。

        Returns:
            下载成功返回文件路径，失败返回 None
        """
        arxiv_id = normalize_arxiv_id(arxiv_id)
        if filename is None:
            filename = f"{arxiv_id}{self.extension}"
        return self.download(self._remote_url(arxiv_id), filename, download_dir)

    def download_by_metadata(
        self,
        metadata,
        download_dir: Optional[str] = None,
    ) -> Optional[DownloadedPaper]:
        """
        通过论文元数据下载，使用标准化文件名（作者_年份_ID）。

        Returns:
            下载成功返回 DownloadedPaper，失败返回 None
        """
        url = metadata.pdf_url if self.kind == "pdf" else self._remote_url(metadata.arxiv_id)
        filename = generate_filename(
            arxiv_id=metadata.arxiv_id.replace("/", "_"),
            author=metadata.authors[0].split()[-1] if metadata.authors else None,
            year=metadata.published_date[:4] if metadata.published_date else None,
            extension=self.extension,
        )

        filepath = self.download(url, filename, download_dir)
        if not filepath:
            return None

        file_size = Path(filepath).stat().st_size if Path(filepath).exists() else None
        return DownloadedPaper(
            metadata=metadata,
            local_pdf_path=filepath,
            file_size=file_size,
        )
