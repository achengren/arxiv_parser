# arXiv Parser 系统架构文档

## 📋 项目概述

arXiv Parser 是一个学术论文自动解析与知识提取系统，支持从 arXiv 获取论文、解析 PDF、使用 LLM 分析内容，并生成结构化数据。

**核心能力：**
- ✅ 自动下载 arXiv 论文 PDF
- ✅ 提取文本、图片、章节结构
- ✅ LLM 智能分析（DeepSeek API）
- ✅ 生成摘要、创新点、问答对
- ✅ 结构化数据导出（JSON/Markdown）
- ✅ SQLite 数据库持久化存储

---

## 🏗️ 系统架构

### 整体架构图

```
┌─────────────────────────────────────────────────────────────┐
│                      arXiv Parser System                    │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌──────────┐    ┌──────────┐    ┌──────────┐              │
│  │ Fetcher  │ -> │Downloader│ -> │  Parser  │              │
│  └──────────┘    └──────────┘    └──────────┘              │
│                                       ↓                     │
│  ┌──────────┐    ┌──────────┐    ┌──────────┐              │
│  │ Exporter │ <- │ Analyzer │ <- │ Database │              │
│  └──────────┘    └──────────┘    └──────────┘              │
│                                                             │
├─────────────────────────────────────────────────────────────┤
│                    Interface Adapters                       │
│  ┌────────────────┐         ┌────────────────┐             │
│  │   Outbound     │         │    Inbound     │             │
│  │ (DeepSeek API) │         │ (CLI/REST/MCP) │             │
│  └────────────────┘         └────────────────┘             │
└─────────────────────────────────────────────────────────────┘
```

### 分层设计

| 层级 | 职责 | 核心组件 |
|------|------|----------|
| **数据层** | 数据模型定义与持久化 | models.py, database.py |
| **功能层** | 核心业务逻辑 | fetcher/downloader/parser/analyzer/exporter |
| **接口层** | 外部系统集成 | adapters/outbound, adapters/inbound |
| **应用层** | 用户交互 | __main__.py (CLI) |

---

## 📦 核心模块详解

### 1. 数据模型层 (arxiv_parser/models.py)

定义系统所有数据结构，确保模块间数据流转一致。

#### 核心数据模型

```python
PaperMetadata      # 论文元数据（arXiv API）
    ↓
DownloadedPaper    # 下载后的论文（PDF 路径）
    ↓
ParsedPaper        # 解析后的论文（文本/图片/表格）
    ↓
AnalyzedPaper      # LLM 分析结果（摘要/创新点/问答对）
    ↓
OutputData         # 最终输出（JSON/Markdown）
```

#### 关键模型说明

| 模型 | 用途 | 关键字段 |
|------|------|----------|
| **PaperMetadata** | 论文元数据 | arxiv_id, title, authors, abstract, categories, pdf_url |
| **DownloadedPaper** | 下载状态 | metadata, local_pdf_path, download_time, file_size |
| **ParsedPaper** | 解析结果 | full_text, sections, images, tables, references, page_count |
| **AnalyzedPaper** | 分析结果 | summary_zh/en, innovations, methodology, qa_pairs, keywords |
| **OutputData** | 输出格式 | structured_knowledge, sections, analysis, process_time |
| **AnalysisResult** | 数据库缓存 | arxiv_id, llm_model, summary, scores, created_at |

#### 枚举类型

- **AnalysisType**: SUMMARY, INNOVATION, METHODOLOGY, EXPERIMENTS, QA_GENERATION, NOVELTY_SCORING
- **PaperStatus**: PENDING, COMPLETED, FAILED

---

### 2. 数据库层 (arxiv_parser/database.py)

SQLite 数据库管理，支持元数据存储、分析结果缓存、状态跟踪。

#### 数据库表结构

```sql
-- 论文元数据表
papers (
    arxiv_id TEXT PRIMARY KEY,
    title, authors, abstract, categories,
    pdf_url, published_date, updated_date,
    local_pdf_path, image_dir,
    download_status, parse_status, analyze_status,
    file_size, page_count,
    created_at, updated_at
)

-- LLM 分析结果表（缓存，避免重复调用）
analysis_results (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    arxiv_id TEXT,
    llm_model TEXT,
    summary_zh, summary_en,
    innovations, methodology, experiments, conclusions,
    novelty_score, quality_score,
    keywords, analysis_time,
    created_at
)

-- 问答对表
qa_pairs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    analysis_id INTEGER,
    question, answer, qa_type
)

-- 图片信息表
images (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    arxiv_id TEXT,
    image_path, page_number, caption, image_type
)

-- 表格信息表
tables (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    arxiv_id TEXT,
    table_path, page_number, caption, table_data
)

-- 参考文献表
references_table (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    arxiv_id TEXT,
    ref_id, ref_text, ref_title, ref_authors, ref_year
)

-- 论文章节表
sections (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    arxiv_id TEXT,
    section_title, section_level, content, page_start, page_end
)
```

#### DatabaseManager 核心方法

```python
# 元数据操作
save_paper_metadata(metadata)           # 保存论文元数据
get_paper_metadata(arxiv_id)            # 获取论文元数据
paper_exists(arxiv_id)                  # 检查论文是否存在
update_paper_status(arxiv_id, field, status)  # 更新处理状态
search_papers(category, author, keyword)  # 搜索论文

# 分析结果操作
save_analysis_result(arxiv_id, analysis)  # 保存分析结果
get_analysis_result(arxiv_id)             # 获取分析结果

# 统计查询
get_statistics()  # 获取数据库统计信息
```

#### 设计优势

- ✅ **去重机制**：下载前检查 arxiv_id 是否已存在
- ✅ **结果缓存**：LLM 分析结果存入数据库，避免重复调用 API
- ✅ **状态跟踪**：记录每个阶段处理状态（pending/downloaded/parsed/analyzed）
- ✅ **快速查询**：支持按分类、作者、关键词检索
- ✅ **关系管理**：论文-作者-引用的关系清晰
- ✅ **可扩展**：SQLite 可无缝迁移到 PostgreSQL/MySQL

---

### 3. 核心功能层

#### 3.1 论文获取 (arxiv_parser/fetcher.py)

**ArxivFetcher** - 与 arXiv API 交互

```python
# 核心方法
search_by_id(arxiv_id)                    # 通过 arXiv ID 搜索
search_by_query(query, max_results=10)    # 通过关键词搜索

# 返回类型
-> Optional[PaperMetadata]
-> List[PaperMetadata]
```

**技术实现：**
- 使用 `arxiv` 库（>=4.0.0）
- 自动处理 API 延迟（默认 3 秒）
- 支持批量查询

---

#### 3.2 PDF 下载 (arxiv_parser/downloader.py)

**PaperDownloader** - PDF / LaTeX 源文件下载管理（通过 `kind="pdf"/"source"` 区分，默认 `pdf`）

```python
# 核心方法
download_by_id(arxiv_id, output_dir)              # 按 ID 下载
download_by_metadata(metadata, output_dir)        # 按元数据下载
download_multiple(arxiv_ids, output_dir)          # 批量下载

# 返回类型
-> Optional[DownloadedPaper]
-> List[DownloadedPaper]
```

**技术实现：**
- 使用 `requests` 库流式下载
- 自动创建输出目录
- 支持断点续传（待实现）
- 文件大小统计

---

#### 3.3 PDF 解析 (arxiv_parser/parser.py)

**ArxivParser** - PDF 内容提取

```python
# 核心方法
parse_pdf(downloaded)                     # 解析完整论文
extract_text(pdf_path)                    # 提取纯文本
extract_images(pdf_path, output_dir)      # 提取图片

# 返回类型
-> ParsedPaper
-> str
-> List[ImageInfo]
```

**功能清单：**
- ✅ 全文提取（使用 PyMuPDF）
- ✅ 图片提取（保存到文件，记录路径）
- ✅ 章节识别（正则匹配常见章节标题）
- ✅ 参考文献提取（匹配引用格式）
- ⏳ 表格提取（待集成 pdfplumber）

**依赖：**
- PyMuPDF (fitz) >= 1.23.0

---

#### 3.4 LLM 分析 (arxiv_parser/analyzer.py)

**ArxivAnalyzer** - 智能论文分析

```python
# 核心方法
analyze(parsed, analysis_types)           # 完整分析流程
generate_summary(text, language)          # 生成摘要
extract_innovations(text)                 # 提取创新点
generate_qa_pairs(text, num_pairs)        # 生成问答对

# 返回类型
-> AnalyzedPaper
-> str
-> List[str]
-> List[QAPair]
```

**分析功能（由 `AnalysisType` 枚举控制，按需执行）：**
1. **生成摘要** - 中英文摘要（200-300 字）
2. **提取创新点** - 3-5 个主要创新点
3. **分析方法论** - 核心技术和方法（300 字）
4. **提取实验信息** - 实验设置和结果（300 字）
5. **生成问答对** - 5 个帮助理解的问答对
6. **提取关键词** - 5-10 个关键词
7. **提取结论** - 总结主要结论（300 字，`AnalysisType.CONCLUSIONS`）
8. **新颖性评分** - 1-5 分（`AnalysisType.NOVELTY_SCORING`）

**LLM 集成：**
- ✅ **DeepSeek API** - 通过 `build_llm_client(config)` 构建客户端注入
- ⏳ **Ollama** - 本地模型支持（待完善）
- ✅ **模拟模式** - 不注入 `llm_client`（即 `ArxivAnalyzer()`），无需 API

**使用示例：**
```python
from arxiv_parser.config import Config
from adapters.outbound import build_llm_client

# 按配置构建 DeepSeek 客户端并注入
config = Config.from_yaml()
analyzer = ArxivAnalyzer(llm_client=build_llm_client(config))
analyzed = analyzer.analyze(parsed_paper)

# 模拟模式（不消耗 API）
analyzer = ArxivAnalyzer()
analyzed = analyzer.analyze(parsed_paper)
```

**问答对生成机制 (QA Generation)：**

问答对不是模板/规则抽取，而是**纯 LLM 生成**，流程如下：

1. **输入**：论文全文 `text`，取**前 2000 字符**（`analyzer.py` 中 `text[:2000]`）塞进 prompt，非全文。
2. **生成**：调用 `llm_client.complete()`（即配置的 `deepseek-chat`），system prompt 为「你是一位专业的学术论文分析助手，擅长生成帮助理解论文的问答对」，要求返回 JSON 数组，每个元素含 `question` / `answer`。
3. **解析**：从返回内容中抓取 `[...]` 段做 `json.loads`，转成 `QAPair` 对象，`qa_type` **统一写死为 `'general'`**。
4. **数量**：默认 `num_pairs=5`。

**已知限制 / 待改进：**
- 只喂前 2000 字符，长论文的 QA 仅覆盖开头部分。
- `qa_type` 字段写死 `'general'`，未做分类（mock 模式里有 `understanding`/`comparison` 区分，真实 LLM 路径没复用）。
- 无兜底：JSON 解析失败时返回一条「论文内容→原始内容」的占位 QAPair；LLM 调用异常时直接返回空列表。

---

#### 3.5 数据导出 (arxiv_parser/exporter.py)

**ArxivExporter** - 格式化输出

```python
# 核心方法
export(analyzed, output_format, output_path)  # 导出数据
to_json(analyzed)                             # 转换为 JSON
to_markdown(analyzed)                         # 转换为 Markdown

# 返回类型
-> OutputData
-> str
-> str
```

**输出格式：**
- ✅ JSON - 结构化数据，适合程序处理
- ✅ Markdown - 可读性报告，适合人工阅读

> 数据库持久化不再由 exporter 负责，而是由 `PaperPipeline` 在处理流程中完成（exporter 保持纯函数式，只做格式化输出）。

**JSON 输出结构（统一英文键，与数据模型字段一致）：**
```json
{
  "title": "Paper Title",
  "arxiv_id": "2301.12345",
  "categories": ["cs.AI", "cs.LG"],
  "source_url": "https://arxiv.org/abs/2301.12345",
  "pdf_path": "output/pdfs/2301.12345.pdf",
  "full_text": "The dominant sequence transduction models are based on...",
  "structured_knowledge": {
    "authors": ["Author1", "Author2"],
    "published_date": "2024-01-01",
    "methodology": "...",
    "contributions": ["...", "..."],
    "keywords": ["...", "..."]
  },
  "sections": {
    "摘要": {"content": "...", "level": 1},
    "引言": {"content": "...", "level": 1}
  },
  "images": [
    {"image_id": 0, "page_number": 1, "local_path": "...", "caption": null}
  ],
  "tables": [],
  "references": {
    "count": 20,
    "items": [{"ref_id": "1", "text": "..."}]
  },
  "analysis": {
    "summary_zh": "...",
    "summary_en": "...",
    "innovations": ["...", "..."],
    "qa_pairs": [{"question": "...", "answer": "..."}]
  },
  "process_time": "2024-01-01T12:00:00",
  "version": "1.0"
}
```

---

### 4. 接口层 (adapters/)

#### 4.1 Outbound 适配器 (adapters/outbound/)

系统调用外部服务的适配器。

**DeepSeekAdapter** - DeepSeek API 适配器

```python
class DeepSeekAdapter(LLMAdapter):
    def __init__(self, api_key=None, model="deepseek-chat", temperature=0.7, max_tokens=2000):
        # 自动从 .env 读取 DEEPSEEK_API_KEY

    def chat(self, messages, **kwargs) -> LLMResponse:
        # 对话接口

    def complete(self, prompt, system_prompt=None, **kwargs) -> LLMResponse:
        # 补全接口
```

**OllamaAdapter** - 本地模型适配器，通过 Ollama 服务调用（无需 API Key）。

**LLMResponse 数据结构：**
```python
@dataclass
class LLMResponse:
    content: str              # 响应内容
    model: str                # 使用的模型
    usage: Dict[str, int]     # Token 使用统计
```

**支持的模型：**
- deepseek-chat（默认）
- deepseek-coder

---

#### 4.2 Inbound 适配器 (adapters/inbound/)

系统被外部调用的适配器。

**已实现：**
- ✅ MCP Server - 基于官方 mcp SDK，暴露 5 个工具（search / download / info / analyze / get_full_text）

---

### 5. CLI 入口 (arxiv_parser/__main__.py)

命令行工具，支持完整的论文处理流程。

**可用命令：**

```bash
# 下载论文
python -m arxiv_parser download --id 2301.12345

# 查看论文信息
python -m arxiv_parser info --id 2301.12345

# 搜索论文
python -m arxiv_parser search --query "transformer" --max-results 10

# LLM 分析（下载 → 解析 → 分析 → 入库）
python -m arxiv_parser analyze --id 2301.12345 --format json

# 查看数据库统计
python -m arxiv_parser stats
```

**技术实现：**
- 使用 `click` 库构建 CLI
- 使用 `loguru` 记录日志
- 支持配置文件（config/config.yaml）

---

### 6. 配置管理 (arxiv_parser/config.py)

分层配置系统，优先级从低到高：

1. **默认配置** - 代码中定义的默认值
2. **基础配置** - config/config.yaml（上传到 Git）
3. **本地配置** - config/config.local.yaml（不上传，覆盖基础配置）
4. **环境变量** - .env 文件（不上传，最高优先级）

**配置类：**

```python
@dataclass
class Config:
    arxiv: ArxivConfig      # arXiv API 配置
    paths: PathConfig       # 路径配置
    llm: LLMConfig          # LLM 配置
    output: OutputConfig    # 输出配置
```

**配置示例：**

```yaml
# config/config.yaml
arxiv:
  delay_seconds: 3.0
  max_results: 50

paths:
  pdf_dir: "output/pdfs"
  image_dir: "output/images"
  result_dir: "output/results"

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

```bash
# .env（敏感信息）
DEEPSEEK_API_KEY=sk-your-actual-key-here
```

---

## 🔄 数据流转

### 完整处理流程

```
1. 用户输入 arXiv ID
   ↓
2. ArxivFetcher.search_by_id()
   → 返回 PaperMetadata
   ↓
3. PaperDownloader.download_by_metadata()
   → 下载 PDF 到本地
   → 返回 DownloadedPaper
   ↓
4. ArxivParser.parse_pdf()
   → 提取文本、图片、章节
   → 返回 ParsedPaper
   ↓
5. ArxivAnalyzer.analyze()
   → 调用 DeepSeek API 分析
   → 返回 AnalyzedPaper
   ↓
6. ArxivExporter.export()
   → 生成 JSON/Markdown 文件
   → 返回 OutputData
   ↓
7. 输出结果文件
```

> 上述步骤通常由 `PaperPipeline.process()` 统一编排，并在每个阶段（元数据 → 下载 → 解析 → 分析）写入数据库；exporter 仅负责把结果写成 JSON/Markdown 文件。

### 状态跟踪

每个处理阶段（下载/解析/分析）的状态独立记录在数据库中：

```
download_status / parse_status / analyze_status:

pending → completed
   ↓
failed
```

每个阶段的状态都记录在数据库中，支持断点续处理。

---

## 📁 项目结构

```
arxiv_parser/
├── arxiv_parser/              # 核心包
│   ├── __init__.py            # 包初始化（导出所有 API）
│   ├── __main__.py            # CLI 入口
│   ├── config.py              # 配置管理
│   ├── models.py              # 数据模型定义
│   ├── database.py            # 数据库管理
│   ├── utils.py               # 工具函数
│   ├── fetcher.py             # arXiv API 获取
│   ├── downloader.py          # PDF / 源文件下载
│   ├── parser.py              # PDF 内容解析
│   ├── analyzer.py            # LLM 智能分析
│   ├── exporter.py            # 数据格式化输出
│   └── pipeline.py            # 端到端处理流水线
│
├── adapters/                  # 接口适配器
│   ├── __init__.py
│   ├── outbound/              # 调用外部服务
│   │   ├── __init__.py
│   │   ├── llm_base.py          # LLM 适配器基类
│   │   ├── deepseek_adapter.py  # DeepSeek API 适配器
│   │   └── ollama_adapter.py    # Ollama 本地模型适配器
│   └── inbound/               # 被外部调用
│       ├── __init__.py
│       └── mcp_server.py        # MCP server
│
├── config/                    # 配置文件
│   ├── config.yaml            # 基础配置
│   └── config.local.yaml.example  # 本地配置模板
│
├── tests/                     # 单元测试
├── docs/                      # 文档（MCP_GUIDE / RUN / SYSTEM_FRAMEWORK）
│
├── output/                    # 运行时输出（不上传）
│   ├── papers.db              # SQLite 数据库
│   ├── pdfs/                  # 下载的 PDF 文件
│   ├── images/                # 提取的图片
│   └── results/               # 输出的 JSON/Markdown
│
├── .env                       # 环境变量（不上传）
├── .env.example               # 环境变量模板
├── .gitignore                 # Git 忽略配置
├── .mcp.json                  # MCP server 配置
├── mcp_launch.sh              # MCP 启动脚本
│
├── pyproject.toml             # 项目元数据与依赖
├── environment.yml            # Conda 环境配置
├── deploy.sh                  # 部署脚本（唯一 setup 入口）
├── quickstart.py              # 快速启动检查脚本
│
├── README.md                  # 项目说明
└── ROADMAP.md                 # 开发路线图
```

---

## 🛠️ 技术栈

| 类别 | 技术 | 版本 | 用途 |
|------|------|------|------|
| **语言** | Python | >=3.8 | 主要开发语言 |
| **arXiv API** | arxiv | >=4.0.0 | 论文元数据获取 |
| **PDF 解析** | PyMuPDF | >=1.23.0 | 文本/图片提取 |
| **表格提取** | pdfplumber | >=0.9.0 | 表格识别（待集成） |
| **LLM API** | requests | >=2.28.0 | DeepSeek API 调用 |
| **数据库** | sqlite3 | 内置 | 数据持久化 |
| **配置管理** | pyyaml | >=6.0 | YAML 配置解析 |
| **CLI** | click | >=8.0 | 命令行工具 |
| **日志** | loguru | >=0.7.0 | 日志记录 |
| **环境变量** | python-dotenv | >=1.0.0 | .env 文件加载 |

---

## 🚀 快速开始

### 1. 安装依赖

```bash
# 推荐：一键部署脚本（自动建 conda 环境并安装全部依赖）
./deploy.sh

# 或手动安装（依赖统一由 pyproject.toml 管理）
pip install -e ".[mcp]"
```

### 2. 配置环境变量

```bash
# 复制模板
cp .env.example .env

# 编辑 .env，填入 DeepSeek API Key
DEEPSEEK_API_KEY=sk-your-actual-key-here
```

### 3. 使用 CLI

```bash
# 完整处理流程（下载 → 解析 → 分析 → 入库）
python -m arxiv_parser analyze --id 1706.03762

# 查看数据库统计
python -m arxiv_parser stats
```

### 4. 使用 Python API

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

# 2. 下载 PDF
downloader = PaperDownloader(download_dir=config.paths.pdf_dir)
downloaded = downloader.download_by_metadata(metadata)

# 3. 解析 PDF
parser = ArxivParser(image_output_dir=config.paths.image_dir)
parsed = parser.parse_pdf(downloaded)

# 4. LLM 分析
analyzer = ArxivAnalyzer(llm_client=build_llm_client(config))
analyzed = analyzer.analyze(parsed)

# 5. 导出结果
exporter = ArxivExporter(output_dir=config.paths.result_dir)
output = exporter.export(analyzed, output_format="json")

print(f"✓ 处理完成: {output.title}")
```

---

## 🎯 系统特点

1. **模块化设计** - 每个模块职责清晰，易于扩展和维护
2. **接口规范** - LLMAdapter 抽象基类定义统一接口，支持多种 LLM 实现
3. **数据库支持** - SQLite 存储元数据和分析结果，支持快速查询
4. **状态跟踪** - 记录每个阶段处理状态，支持断点续处理
5. **LLM 集成** - DeepSeek API 智能分析，支持模拟模式
6. **CLI 工具** - 命令行直接使用，无需编写代码
7. **配置灵活** - 分层配置系统，支持 YAML 和环境变量
8. **安全可靠** - 敏感信息隔离（.env），Git 忽略配置

---

## ⚠️ 待完善功能

### 高优先级

1. **表格提取** - 集成 pdfplumber，提取论文中的表格
2. **图片描述** - 使用多模态 LLM 生成图片 caption
3. **批量处理** - 支持批量下载和分析多篇论文

### 中优先级

4. **断点续传** - PDF 下载支持断点续传
5. **错误重试** - API 调用失败自动重试
6. **进度显示** - CLI 显示处理进度条
7. **多语言支持** - 支持更多语言的摘要生成

### 低优先级

8. **分布式处理** - 支持多进程/多线程并行处理
9. **Web 界面** - 简单的 Web 界面展示结果
10. **论文推荐** - 基于分析结果推荐相关论文
11. **知识图谱** - 将分析结果导入 Neo4j 构建知识图谱

---

## 📝 开发指南

### 添加新的 LLM 提供商

1. 在 `adapters/outbound/` 创建新的适配器文件
2. 继承 `LLMAdapter` 基类
3. 实现 `chat()` 和 `complete()` 方法
4. 在 `__init__.py` 中导出

### 添加新的输出格式

1. 在 `ArxivExporter` 中添加新的方法
2. 实现 `to_xxx()` 方法
3. 在 `export()` 方法中添加新的分支

### 扩展数据库表

1. 在 `database.py` 的 `_init_database()` 中添加新的表定义
2. 添加对应的 CRUD 方法
3. 更新 `models.py` 中的数据模型

---

## 🔗 相关资源

- **arXiv API 文档**: https://arxiv.org/help/api
- **DeepSeek API 文档**: https://platform.deepseek.com/api-docs/
- **PyMuPDF 文档**: https://pymupdf.readthedocs.io/
- **Click 文档**: https://click.palletsprojects.com/
- **Loguru 文档**: https://loguru.readthedocs.io/

---

## 📄 许可证

MIT License

---

## 👥 贡献者

- arXiv Parser Team

---

**最后更新**: 2024-11-09  
**版本**: 0.3.0
