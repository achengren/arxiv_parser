#!/usr/bin/env python3
"""
arXiv Parser 快速启动脚本（健康检查）
用法：python3 quickstart.py
"""

import sys
from pathlib import Path

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent))


def check_dependencies():
    """检查依赖"""
    print("=" * 60)
    print("检查依赖...")
    print("=" * 60)

    required_packages = {
        'requests': 'HTTP 请求',
        'yaml': 'YAML 配置',
        'click': 'CLI 工具',
        'loguru': '日志处理',
        'arxiv': 'arXiv API',
        'fitz': 'PDF 解析',
        'dotenv': '环境变量',
    }

    missing = []
    for package, desc in required_packages.items():
        try:
            __import__(package)
            print(f"✓ {package:15s} - {desc}")
        except ImportError:
            print(f"✗ {package:15s} - 未安装")
            missing.append(package)

    if missing:
        print("\n⚠ 缺少依赖，请运行部署脚本：")
        print("  ./deploy.sh")
        return False

    print("\n✓ 所有依赖已安装")
    return True


def check_config(config):
    """检查配置（.env + API Key）"""
    print("\n" + "=" * 60)
    print("检查配置...")
    print("=" * 60)

    if not Path('.env').exists():
        print("✗ .env 文件不存在")
        print("\n请创建 .env 文件：")
        print("  cp .env.example .env")
        print("  # 然后编辑 .env 填入 DEEPSEEK_API_KEY")
        return False

    print(f"✓ LLM provider: {config.llm.provider}, model: {config.llm.model}")

    if config.llm.provider == "deepseek":
        api_key = config.llm.api_key
        if not api_key:
            print("✗ DEEPSEEK_API_KEY 未配置")
            print("\n请编辑 .env 文件，添加：")
            print("  DEEPSEEK_API_KEY=sk-your-actual-key-here")
            return False
        print(f"✓ API Key: {api_key[:10]}...{api_key[-4:]}")
    else:
        print("✓ 使用本地 LLM，无需 API Key")

    return True


def test_basic_import():
    """测试基本导入"""
    print("\n" + "=" * 60)
    print("测试模块导入...")
    print("=" * 60)

    try:
        from adapters.outbound import build_llm_client
        print("✓ build_llm_client 导入成功")

        from arxiv_parser import (
            ArxivFetcher, PaperDownloader, ArxivParser,
            ArxivAnalyzer, ArxivExporter, DatabaseManager
        )
        print("✓ 核心模块导入成功")

        return True
    except Exception as e:
        print(f"✗ 导入失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_api_connection(config):
    """测试 API 连接"""
    print("\n" + "=" * 60)
    print("测试 LLM API 连接...")
    print("=" * 60)

    try:
        from adapters.outbound import build_llm_client

        adapter = build_llm_client(config)
        if adapter is None:
            print("⚠ 无法构建 LLM 客户端，将使用 mock 模式")
            return False

        print(f"使用模型: {adapter.model}")
        print("发送测试消息...")
        response = adapter.chat([
            {"role": "user", "content": "你好，请用一句话介绍你自己。"}
        ])

        print("✓ API 连接成功！")
        print(f"\n模型回复: {response.content}")
        print(f"Token 使用: {response.usage}")

        return True
    except Exception as e:
        print(f"✗ API 连接失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def show_usage():
    """显示使用方法"""
    print("\n" + "=" * 60)
    print("📖 使用方法")
    print("=" * 60)

    print("""
1. 命令行使用：

   # 下载论文
   python3 -m arxiv_parser download --id 1706.03762

   # 查看论文信息
   python3 -m arxiv_parser info --id 1706.03762

   # 搜索论文
   python3 -m arxiv_parser search --query "transformer" --max-results 5

   # 完整处理流程（下载 → 解析 → 分析 → 入库）
   python3 -m arxiv_parser analyze --id 1706.03762 --format json

   # 查看数据库统计
   python3 -m arxiv_parser stats

2. Python API 使用：

   from arxiv_parser import ArxivFetcher, ArxivAnalyzer
   from arxiv_parser.config import Config
   from adapters.outbound import build_llm_client

   config = Config.from_yaml()

   # 获取论文
   fetcher = ArxivFetcher(config=config.arxiv)
   metadata = fetcher.search_by_id("1706.03762")

   # 分析论文
   analyzer = ArxivAnalyzer(llm_client=build_llm_client(config))
   # ... 完整流程见 docs/SYSTEM_FRAMEWORK.md

3. 输出目录：

   output/
   ├── pdfs/          # 下载的 PDF 文件
   ├── images/        # 提取的图片
   ├── results/       # 输出的 JSON/Markdown
   └── papers.db      # SQLite 数据库

4. 配置文件：

   .env                        # 环境变量（API Key）
   config/config.yaml          # 基础配置
   config/config.local.yaml    # 本地配置（可选）
""")


def main():
    """主函数"""
    print("\n" + "=" * 60)
    print("🚀 arXiv Parser 快速启动")
    print("=" * 60)

    # 检查依赖
    if not check_dependencies():
        sys.exit(1)

    # 加载配置（会读取 .env 与环境变量）
    from arxiv_parser.config import Config
    config = Config.from_yaml()

    # 检查配置
    if not check_config(config):
        sys.exit(1)

    # 测试导入
    if not test_basic_import():
        sys.exit(1)

    # 测试 API 连接
    if not test_api_connection(config):
        print("\n⚠ API 连接失败，但仍可以使用 mock 模式")

    # 显示使用方法
    show_usage()

    print("\n" + "=" * 60)
    print("✓ 系统就绪！可以开始使用了")
    print("=" * 60 + "\n")


if __name__ == "__main__":
    main()
