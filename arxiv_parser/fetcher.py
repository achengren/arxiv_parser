"""
arXiv 论文获取模块
基于 arxiv.py 库实现论文搜索和元数据获取
"""

import arxiv
from typing import List, Optional
from loguru import logger

from .config import ArxivConfig
from .models import PaperMetadata
from .utils import parse_arxiv_id


class ArxivFetcher:
    """arXiv 论文获取器"""

    def __init__(self, config: Optional[ArxivConfig] = None):
        """
        初始化获取器

        Args:
            config: ArxivConfig 配置对象（可选，缺省用默认值）
        """
        config = config or ArxivConfig()
        self.client = arxiv.Client(delay_seconds=config.delay_seconds, num_retries=3)
        self.max_results = config.max_results
        logger.info(f"ArxivFetcher initialized with delay={config.delay_seconds}s, max_results={config.max_results}")
    
    def search_by_id(self, arxiv_id: str) -> Optional[PaperMetadata]:
        """
        通过 arXiv ID 搜索单篇论文
        
        Args:
            arxiv_id: arXiv 论文 ID，如 "2301.12345" 或 "2301.12345v1"
            
        Returns:
            PaperMetadata 或 None
        """
        # 解析纯 ID
        pure_id = parse_arxiv_id(arxiv_id)
        if pure_id:
            arxiv_id = pure_id
        
        logger.info(f"Searching paper by ID: {arxiv_id}")
        
        try:
            search = arxiv.Search(id_list=[arxiv_id])
            results = list(self.client.results(search))
            
            if not results:
                logger.warning(f"No paper found with ID: {arxiv_id}")
                return None
            
            return self._parse_result(results[0])
            
        except Exception as e:
            logger.error(f"Error searching paper {arxiv_id}: {e}")
            return None
    
    def search_by_query(
        self, 
        query: str, 
        max_results: Optional[int] = None,
        sort_by: arxiv.SortCriterion = arxiv.SortCriterion.Relevance
    ) -> List[PaperMetadata]:
        """
        通过关键词搜索论文
        
        Args:
            query: 搜索关键词
            max_results: 最大结果数
            sort_by: 排序方式
            
        Returns:
            论文元数据列表
        """
        if max_results is None:
            max_results = self.max_results
            
        logger.info(f"Searching papers by query: '{query}', max_results={max_results}")
        
        try:
            search = arxiv.Search(
                query=query,
                max_results=max_results,
                sort_by=sort_by
            )
            
            results = []
            for result in self.client.results(search):
                results.append(self._parse_result(result))
            
            logger.info(f"Found {len(results)} papers")
            return results
            
        except Exception as e:
            logger.error(f"Error searching papers with query '{query}': {e}")
            return []
    
    def search_multiple_ids(self, arxiv_ids: List[str]) -> List[PaperMetadata]:
        """
        批量搜索多篇论文
        
        Args:
            arxiv_ids: arXiv ID 列表
            
        Returns:
            论文元数据列表
        """
        logger.info(f"Searching {len(arxiv_ids)} papers by IDs")
        
        results = []
        for arxiv_id in arxiv_ids:
            paper = self.search_by_id(arxiv_id)
            if paper:
                results.append(paper)
        
        logger.info(f"Successfully fetched {len(results)}/{len(arxiv_ids)} papers")
        return results
    
    def _parse_result(self, result: arxiv.Result) -> PaperMetadata:
        """
        解析 arxiv.Result 为 PaperMetadata
        
        Args:
            result: arxiv.py 返回的结果对象
            
        Returns:
            PaperMetadata
        """
        return PaperMetadata(
            arxiv_id=self._extract_id(result.entry_id),
            title=result.title.replace('\n', ' ').strip(),
            authors=[author.name for author in result.authors],
            abstract=result.summary.replace('\n', ' ').strip(),
            categories=result.categories,
            primary_category=result.primary_category,
            published_date=result.published.strftime("%Y-%m-%d"),
            updated_date=result.updated.strftime("%Y-%m-%d"),
            pdf_url=result.pdf_url,
            entry_id=result.entry_id
        )
    
    def _extract_id(self, entry_id: str) -> str:
        """
        从 entry_id 提取纯 arXiv ID
        
        Args:
            entry_id: 如 "http://arxiv.org/abs/2301.12345v1"
            
        Returns:
            纯 ID，如 "2301.12345v1"
        """
        return entry_id.split("/abs/")[-1]
