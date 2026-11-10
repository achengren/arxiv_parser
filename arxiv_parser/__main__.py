"""CLI 入口"""

import sys
import click
from pathlib import Path

from loguru import logger

from .config import Config
from .models import PaperStatus
from .fetcher import ArxivFetcher
from .downloader import PaperDownloader
from .exporter import ArxivExporter
from .database import DatabaseManager
from .pipeline import PaperPipeline
from adapters.outbound import build_llm_client


# 配置日志
logger.remove()
logger.add(
    sys.stderr,
    format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
    level="INFO"
)
logger.add(
    "logs/arxiv_parser.log",
    rotation="10 MB",
    retention="7 days",
    level="DEBUG"
)


@click.group()
@click.version_option(version='0.3.0')
@click.option('--config', '-c', default='config/config.yaml', help='配置文件路径')
@click.pass_context
def cli(ctx, config):
    """arXiv Paper Parser - 学术论文解析与知识提取工具"""
    ctx.ensure_object(dict)
    ctx.obj['config'] = Config.from_yaml(config)


@cli.command()
@click.option('--id', '-i', required=True, help='arXiv 论文 ID')
@click.option('--output', '-o', default=None, help='输出目录')
@click.pass_context
def download(ctx, id, output):
    """下载论文"""
    config = ctx.obj['config']
    output_dir = output or config.paths.pdf_dir

    fetcher = ArxivFetcher(config=config.arxiv)
    metadata = fetcher.search_by_id(id)
    if not metadata:
        logger.error(f"未找到论文: {id}")
        sys.exit(1)

    downloader = PaperDownloader(download_dir=output_dir)
    downloaded = downloader.download_by_metadata(metadata)
    if not downloaded:
        logger.error("下载失败")
        sys.exit(1)

    db = DatabaseManager(config.paths.db_path)
    db.save_paper_metadata(metadata)
    db.update_paper_status(metadata.arxiv_id, 'download_status', PaperStatus.COMPLETED.value)

    logger.success(f"下载完成: {downloaded.local_pdf_path}")


@cli.command()
@click.option('--id', '-i', required=True, help='arXiv 论文 ID')
@click.pass_context
def info(ctx, id):
    """查看论文信息"""
    config = ctx.obj['config']

    fetcher = ArxivFetcher(config=config.arxiv)
    metadata = fetcher.search_by_id(id)
    if not metadata:
        logger.error(f"未找到论文: {id}")
        sys.exit(1)

    click.echo("\n" + "=" * 80)
    click.echo(f"标题: {metadata.title}")
    click.echo(f"作者: {', '.join(metadata.authors)}")
    click.echo(f"分类: {', '.join(metadata.categories)}")
    click.echo(f"发布日期: {metadata.published_date}")
    click.echo(f"摘要: {metadata.abstract[:200]}...")
    click.echo(f"PDF URL: {metadata.pdf_url}")
    click.echo("=" * 80 + "\n")


@cli.command()
@click.option('--query', '-q', required=True, help='搜索关键词')
@click.option('--max-results', '-n', default=10, help='最大结果数')
@click.pass_context
def search(ctx, query, max_results):
    """搜索论文"""
    config = ctx.obj['config']

    fetcher = ArxivFetcher(config=config.arxiv)
    papers = fetcher.search_by_query(query, max_results=max_results)
    if not papers:
        logger.warning("未找到相关论文")
        return

    click.echo(f"\n找到 {len(papers)} 篇论文:\n")
    for i, paper in enumerate(papers, 1):
        click.echo(f"{i}. [{paper.arxiv_id}] {paper.title}")
        click.echo(f"   作者: {', '.join(paper.authors[:3])}{'...' if len(paper.authors) > 3 else ''}")
        click.echo(f"   分类: {', '.join(paper.categories[:3])}")
        click.echo(f"   日期: {paper.published_date}")
        click.echo("")


@cli.command()
@click.option('--id', '-i', required=True, help='arXiv 论文 ID')
@click.option('--format', '-f', 'output_format', default='json', type=click.Choice(['json', 'markdown']), help='导出格式')
@click.option('--output', '-o', default=None, help='导出目录')
@click.pass_context
def analyze(ctx, id, output_format, output):
    """分析论文（完整流程：下载 → 解析 → LLM 分析 → 入库）"""
    config = ctx.obj['config']

    try:
        pipeline = PaperPipeline(config=config, llm_client=build_llm_client(config))
        analyzed = pipeline.process(id)

        metadata = analyzed.parsed.downloaded.metadata
        click.echo("\n" + "=" * 80)
        click.echo(f"标题: {metadata.title}")
        click.echo(f"arXiv ID: {metadata.arxiv_id}")
        click.echo(f"模型: {analyzed.llm_model}")
        click.echo("=" * 80)

        if analyzed.summary_zh:
            click.echo(f"\n中文摘要:\n{analyzed.summary_zh}\n")
        if analyzed.innovations:
            click.echo("\n创新点:")
            for i, inv in enumerate(analyzed.innovations, 1):
                click.echo(f"  {i}. {inv}")
        if analyzed.keywords:
            click.echo(f"\n关键词: {', '.join(analyzed.keywords)}")
        click.echo("")

        if output:
            exporter = ArxivExporter(output_dir=output)
            exporter.export(analyzed, output_format)

    except Exception as e:
        logger.error(f"分析出错: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


@cli.command()
@click.pass_context
def stats(ctx):
    """查看数据库统计"""
    try:
        config = ctx.obj['config']
        db = DatabaseManager(config.paths.db_path)
        statistics = db.get_statistics()

        click.echo("\n数据库统计:\n")
        click.echo(f"  论文总数: {statistics['total_papers']}")
        click.echo(f"  已下载: {statistics['downloaded_count']}")
        click.echo(f"  已解析: {statistics['parsed_count']}")
        click.echo(f"  已分析: {statistics['analyzed_count']}")

        if statistics.get('top_categories'):
            click.echo("\n  热门分类:")
            for category, count in list(statistics['top_categories'].items())[:5]:
                click.echo(f"    {category}: {count} 篇")

        click.echo("")

    except Exception as e:
        logger.error(f"查询统计出错: {e}")
        sys.exit(1)


def main():
    """主函数"""
    cli(obj={})


if __name__ == '__main__':
    main()
