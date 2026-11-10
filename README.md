# arXiv Paper Parser

学术论文自动解析与知识提取工具，支持从 arXiv 获取论文、解析 PDF、使用 LLM 提取关键信息。

## 核心功能

- **论文搜索**：通过 arXiv ID 或关键词搜索论文
- **自动下载**：下载论文 PDF / LaTeX 源文件
- **PDF 解析**：提取文字、图片、章节、参考文献
- **智能分析**：使用 DeepSeek API 生成摘要、提取创新点与关键词、生成问答对
- **MCP 集成**：支持 Claude Code 等 AI 助手通过 MCP 协议调用
- **数据持久化**：SQLite 数据库存储元数据、解析与分析结果

## 快速开始

### 安装

```bash
# 方式一：conda
conda env create -f environment.yml
conda activate arxiv_parser

# 方式二：pip
pip install -e ".[mcp]"
```

### 配置

```bash
cp .env.example .env
# 编辑 .env，填入 DEEPSEEK_API_KEY
```

### 命令行使用

```bash
# 搜索论文
python -m arxiv_parser search --query "transformer" --max-results 10

# 查看论文信息
python -m arxiv_parser info --id 1706.03762

# 下载论文
python -m arxiv_parser download --id 1706.03762

# 分析论文（下载 → 解析 → LLM 分析 → 入库）
python -m arxiv_parser analyze --id 1706.03762

# 查看数据库统计
python -m arxiv_parser stats
```

### MCP 集成（Claude Code）

项目根目录的 `.mcp.json` 已配置通过 `mcp_launch.sh` 启动 MCP server，Claude Code 会自动加载。

也可手动添加：

```bash
claude mcp add arxiv-parser -s project -- \
  /home/yourname/miniconda3/envs/arxiv_parser/bin/python3 -m adapters.inbound.mcp_server
```

## MCP 工具

| 工具 | 功能 |
|------|------|
| `get_paper_info` | 获取论文元信息（标题、作者、摘要等） |
| `download_paper` | 下载论文 PDF |
| `search_papers` | 在 arXiv 上搜索论文 |
| `analyze_paper` | LLM 分析（摘要、创新点、关键词、问答对等） |
| `get_full_text` | 获取已解析论文的全文 |

详见 [MCP 集成指南](docs/MCP_GUIDE.md)。

## 项目结构

```
arxiv_parser/
├── arxiv_parser/          # 核心功能包
│   ├── fetcher.py         # arXiv API 获取
│   ├── downloader.py      # PDF / 源文件下载
│   ├── parser.py          # PDF 内容解析
│   ├── analyzer.py        # LLM 智能分析
│   ├── exporter.py        # JSON / Markdown 导出
│   ├── pipeline.py        # 端到端处理流水线
│   ├── database.py        # SQLite 持久化
│   ├── models.py          # 数据模型
│   ├── config.py          # 配置管理
│   ├── utils.py           # 工具函数
│   └── __main__.py        # CLI 入口
├── adapters/
│   ├── outbound/          # 调用外部服务（DeepSeek / Ollama）
│   └── inbound/           # 被外部调用（MCP server）
├── config/                # 配置文件
├── docs/                  # 文档
├── tests/                 # 单元测试
└── output/                # 运行时输出（gitignore）
```

## 配置

### 环境变量（.env）

```bash
# DeepSeek API（用于 LLM 分析）
DEEPSEEK_API_KEY=sk-your-key-here

# MCP server 使用的 Python 解释器路径
ARXIV_PARSER_PYTHON=/home/yourname/miniconda3/envs/arxiv_parser/bin/python3

# Ollama 本地服务地址（可选）
OLLAMA_BASE_URL=http://localhost:11434
```

### 应用配置（config/config.yaml）

```yaml
arxiv:
  delay_seconds: 3.0
  max_results: 50
  sort_by: "submittedDate"

paths:
  pdf_dir: "output/pdfs"
  image_dir: "output/images"
  result_dir: "output/results"
  source_dir: "output/sources"
  log_dir: "logs"
  db_path: "output/papers.db"

llm:
  provider: "deepseek"        # deepseek / ollama
  model: "deepseek-chat"
  temperature: 0.3
  max_tokens: 4000

output:
  format: "json"
  language: "zh"
```

## 文档

- [MCP 集成指南](docs/MCP_GUIDE.md)
- [系统架构](docs/SYSTEM_FRAMEWORK.md)
- [运行指南](docs/RUN.md)
- [开发路线图](ROADMAP.md)

## 许可证

MIT License
