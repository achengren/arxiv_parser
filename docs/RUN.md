# 🚀 快速运行指南

## 步骤 1: 安装依赖

### 方式一：使用部署脚本（推荐）

```bash
./deploy.sh
```

### 方式二：手动安装

```bash
# 使用 pip
pip install -e ".[mcp]"

# 或使用 conda
conda env create -f environment.yml
conda activate arxiv_parser
pip install -e ".[mcp]"
```

## 步骤 2: 检查系统

```bash
python3 quickstart.py
```

这个脚本会检查：
- ✓ 依赖是否安装
- ✓ API Key 是否配置
- ✓ 模块是否可以导入
- ✓ DeepSeek API 是否可以连接

## 步骤 3: 运行项目

### 方式一：命令行工具

```bash
# 1. 下载论文
python3 -m arxiv_parser download --id 1706.03762

# 2. 查看论文信息
python3 -m arxiv_parser info --id 1706.03762

# 3. 搜索论文
python3 -m arxiv_parser search --query "transformer" --max-results 5

# 4. 完整处理流程（推荐）
python3 -m arxiv_parser analyze --id 1706.03762 --format json
```

### 方式二：Python API

```python
from arxiv_parser import (
    ArxivFetcher, PaperDownloader, ArxivParser,
    ArxivAnalyzer, ArxivExporter
)
from arxiv_parser.config import Config
from adapters.outbound import build_llm_client

config = Config.from_yaml()

# 1. 获取论文
fetcher = ArxivFetcher(config=config.arxiv)
metadata = fetcher.search_by_id("1706.03762")
print(f"论文标题: {metadata.title}")

# 2. 下载 PDF
downloader = PaperDownloader(download_dir=config.paths.pdf_dir)
downloaded = downloader.download_by_metadata(metadata)
print(f"PDF 保存到: {downloaded.local_pdf_path}")

# 3. 解析 PDF
parser = ArxivParser(image_output_dir=config.paths.image_dir)
parsed = parser.parse_pdf(downloaded)
print(f"解析完成: {parsed.page_count} 页")

# 4. LLM 分析
analyzer = ArxivAnalyzer(llm_client=build_llm_client(config))
analyzed = analyzer.analyze(parsed)
print(f"分析完成: {len(analyzed.innovations)} 个创新点")

# 5. 导出结果
exporter = ArxivExporter(output_dir=config.paths.result_dir)
output = exporter.export(analyzed, output_format="json")
print(f"✓ 结果已导出到: output/results/{output.arxiv_id}.json")
```

## 步骤 4: 查看结果

```bash
# 查看输出的 JSON 文件
ls output/results/
cat output/results/1706.03762.json

# 查看数据库统计
python3 -m arxiv_parser stats

# 查看提取的图片
ls output/images/
```

## 常用命令

```bash
# 搜索论文
python3 -m arxiv_parser search --query "large language model" --max-results 10

# 查看论文信息
python3 -m arxiv_parser info --id 2301.12345

# 下载单篇论文
python3 -m arxiv_parser download --id 2301.12345

# LLM 分析（下载 → 解析 → 分析 → 入库）
python3 -m arxiv_parser analyze --id 1706.03762 --format json

# 查看数据库统计
python3 -m arxiv_parser stats

# 查看帮助
python3 -m arxiv_parser --help
```

## 输出目录结构

```
output/
├── pdfs/              # 下载的 PDF 文件
│   └── 1706.03762.pdf
├── images/            # 提取的图片
│   └── 1706.03762/
│       ├── page1_img1.png
│       └── page2_img1.png
├── results/           # 输出的 JSON/Markdown
│   ├── 1706.03762.json
│   └── 1706.03762.md
└── papers.db          # SQLite 数据库
```

## 配置文件

### .env（必需）

```bash
DEEPSEEK_API_KEY=sk-your-actual-key-here
```

### config/config.yaml（可选）

```yaml
arxiv:
  delay_seconds: 3.0
  max_results: 50

paths:
  pdf_dir: "output/pdfs"
  image_dir: "output/images"
  result_dir: "output/results"
  source_dir: "output/sources"
  db_path: "output/papers.db"

llm:
  provider: "deepseek"
  model: "deepseek-chat"
  temperature: 0.3
  max_tokens: 4000

output:
  format: "json"
  language: "zh"
  include_qa: true
  qa_count: 5
```

## 故障排查

### 问题 1: 依赖安装失败

```bash
# 升级 pip
python3 -m pip install --upgrade pip

# 使用国内镜像
pip install -i https://pypi.tuna.tsinghua.edu.cn/simple requests pyyaml click loguru arxiv PyMuPDF tqdm python-dotenv
```

### 问题 2: API 连接失败

```bash
# 检查网络连接
curl https://api.deepseek.com

# 检查 API Key
cat .env | grep DEEPSEEK_API_KEY

# 测试 API
python3 quickstart.py
```

### 问题 3: PDF 解析失败

```bash
# 检查 PyMuPDF 是否正确安装
python3 -c "import fitz; print(fitz.__version__)"

# 重新安装
pip uninstall PyMuPDF
pip install PyMuPDF
```

### 问题 4: 模块导入失败

```bash
# 检查 Python 路径
python3 -c "import sys; print(sys.path)"

# 确保在项目根目录运行
cd /path/to/arxiv_parser
python3 -m arxiv_parser --help
```

## 下一步

- 📖 阅读 [SYSTEM_FRAMEWORK.md](SYSTEM_FRAMEWORK.md) 了解系统架构
- 📖 阅读 [README.md](README.md) 了解项目概述
- 🔧 修改 config/config.yaml 自定义配置
- 🚀 尝试处理不同的论文

## 示例论文

```bash
# Attention Is All You Need (Transformer 论文)
python3 -m arxiv_parser analyze --id 1706.03762

# BERT 论文
python3 -m arxiv_parser analyze --id 1810.04805

# GPT-3 论文
python3 -m arxiv_parser analyze --id 2005.14165
```

---

**提示**: 首次运行会下载 PDF 和调用 API，可能需要几分钟时间。
