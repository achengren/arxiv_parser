# MCP 集成指南

本文档详细介绍如何将 arxiv-parser 系统集成到支持 MCP (Model Context Protocol) 的 AI 助手中。

## 目录

- [什么是 MCP](#什么是-mcp)
- [前置要求](#前置要求)
- [配置步骤](#配置步骤)
- [工具说明](#工具说明)
- [使用示例](#使用示例)
- [故障排查](#故障排查)
- [高级配置](#高级配置)

---

## 什么是 MCP

**MCP (Model Context Protocol)** 是一种开放的标准化协议，允许 AI 助手（如 Claude Code、Cursor 等）安全地调用外部工具和服务。

通过 MCP，你可以：
- 🗣️ 用自然语言控制论文分析系统
- 🤖 让 AI 自动调用工具完成任务
- 🔧 无需编写代码即可集成

**架构示意：**

```
用户 (自然语言)
  ↓
Claude Code / AI 助手
  ↓ MCP 协议
arxiv-parser MCP Server
  ↓
核心功能模块
  ├─ 论文搜索 (arxiv API)
  ├─ PDF 下载
  ├─ 内容解析 (PyMuPDF)
  └─ LLM 分析 (DeepSeek API)
```

---

## 前置要求

### 1. 环境要求

- Python >= 3.8
- Conda 环境（推荐）
- Claude Code 或其他支持 MCP 的 AI 助手

### 2. 依赖安装

```bash
# 激活 conda 环境
conda activate arxiv_parser

# 安装依赖
pip install -e ".[mcp]"

# 验证安装
python -m arxiv_parser --version
```

### 3. API 配置

编辑 `.env` 文件：

```bash
# DeepSeek API（用于论文分析）
DEEPSEEK_API_KEY=sk-your-deepseek-api-key
```

---

## 配置步骤

### 方式一：命令行配置（推荐）

```bash
# 1. 获取 Python 完整路径
conda activate arxiv_parser
which python3
# 输出：/home/user/miniconda3/envs/arxiv_parser/bin/python3

# 2. 添加 MCP 服务器到 Claude Code
claude mcp add arxiv-parser -s project -- /home/user/miniconda3/envs/arxiv_parser/bin/python3 -m adapters.inbound.mcp_server

# 3. 验证配置
claude mcp list
# 应该看到：arxiv-parser - ✓ Connected
```

### 方式二：手动配置文件

在项目根目录创建或编辑 `.mcp.json`：

```json
{
  "mcpServers": {
    "arxiv-parser": {
      "type": "stdio",
      "command": "/home/user/miniconda3/envs/arxiv_parser/bin/python3",
      "args": [
        "-m",
        "adapters.inbound.mcp_server"
      ],
      "cwd": "/home/user/arxiv_parser",
      "env": {
        "PYTHONPATH": "/home/user/arxiv_parser"
      }
    }
  }
}
```

**重要字段说明：**

| 字段 | 说明 | 示例 |
|------|------|------|
| `command` | Python 解释器的完整路径 | `/home/user/miniconda3/envs/arxiv_parser/bin/python3` |
| `args` | 启动参数 | `["-m", "adapters.inbound.mcp_server"]` |
| `cwd` | 工作目录（项目根目录） | `/home/user/arxiv_parser` |
| `env` | 环境变量（可选） | `{"PYTHONPATH": "..."}` |

---

## 工具说明

### 1. get_paper_info

**功能：** 获取论文的元信息（标题、作者、摘要、分类等）

**参数：**
- `arxiv_id` (string, 必填): arXiv 论文 ID

**返回示例：**
```json
{
  "success": true,
  "data": {
    "title": "Attention Is All You Need",
    "authors": ["Ashish Vaswani", "Noam Shazeer", ...],
    "abstract": "The dominant sequence transduction models...",
    "published_date": "2017-06-12",
    "categories": ["cs.CL"],
    "pdf_url": "https://arxiv.org/pdf/1706.03762"
  }
}
```

### 2. download_paper

**功能：** 从 arXiv 下载论文 PDF

**参数：**
- `arxiv_id` (string, 必填): arXiv 论文 ID

**返回示例：**
```json
{
  "success": true,
  "message": "论文已下载: output/pdfs/1706.03762.pdf"
}
```

### 3. search_papers

**功能：** 在 arXiv 上搜索论文

**参数：**
- `query` (string, 必填): 搜索关键词
- `max_results` (integer, 可选): 最大结果数，默认 10

**返回示例：**
```json
{
  "success": true,
  "count": 10,
  "data": [
    {
      "arxiv_id": "1706.03762",
      "title": "Attention Is All You Need",
      "authors": ["Ashish Vaswani", ...],
      "published_date": "2017-06-12"
    },
    ...
  ]
}
```

### 4. analyze_paper ⭐

**功能：** 使用 LLM（DeepSeek）分析论文内容，生成摘要、提取创新点和关键词

**参数：**
- `arxiv_id` (string, 必填): arXiv 论文 ID
- `analysis_types` (array, 可选): 分析类型列表

**支持的分析类型：**

| 类型 | 说明 |
|------|------|
| `summary` | 生成中英文摘要 |
| `innovations` | 提取创新点 |
| `keywords` | 提取关键词 |
| `methodology` | 提取方法论 |
| `experiments` | 提取实验内容 |
| `qa_pairs` | 生成问答对 |
| `conclusions` | 提取结论 |
| `novelty` | 新颖性评分（1-5 分） |

**默认分析类型：** `["summary", "innovations", "keywords", "qa_pairs"]`

**返回示例：**
```json
{
  "success": true,
  "arxiv_id": "1706.03762",
  "title": "Attention Is All You Need",
  "summary_zh": "本文提出了一种新的简单网络架构——Transformer...",
  "summary_en": "We propose a new simple network architecture...",
  "innovations": [
    "提出了 Transformer 架构，完全基于注意力机制",
    "引入了多头注意力机制",
    "使用位置编码代替循环和卷积"
  ],
  "keywords": ["transformer", "attention", "neural network"],
  "llm_model": "deepseek-chat",
  "analysis_time": "2026-11-09T23:10:00"
}
```

**工作流程：**
1. 自动下载论文 PDF
2. 解析 PDF 提取全文
3. 调用 DeepSeek API 进行分析
4. 返回结构化分析结果

### 5. get_full_text

**功能：** 获取已解析论文的全文（需先运行 `analyze_paper` 解析入库）

**参数：**
- `arxiv_id` (string, 必填): arXiv 论文 ID（支持不带版本号，如 `1706.03762` 匹配 `1706.03762v7`）

**返回示例：**
```json
{
  "success": true,
  "arxiv_id": "1706.03762",
  "length": 39512,
  "full_text": "The dominant sequence transduction models are based on..."
}
```

---

## 使用示例

### 基础使用

在 Claude Code 中直接用自然语言：

```
# 获取论文信息
用户：帮我查看论文 1706.03762 的信息
Claude：[自动调用 get_paper_info 工具]

# 下载论文
用户：下载这篇论文 2301.12345
Claude：[自动调用 download_paper 工具]

# 搜索论文
用户：搜索关于 RAG 的最新论文，最多5篇
Claude：[自动调用 search_papers 工具]
```

### 高级使用

```
# 完整分析流程
用户：帮我分析论文 1706.03762，提取摘要、创新点和关键词
Claude：[自动调用 analyze_paper 工具，使用 DeepSeek API]

# 指定分析类型
用户：分析这篇论文的方法论和实验部分：2301.12345
Claude：[调用 analyze_paper，analysis_types=["methodology", "experiments"]]

# 批量处理
用户：下载并分析最近关于 transformer 的10篇论文
Claude：[
  1. 调用 search_papers 搜索论文
  2. 循环调用 analyze_paper 分析每篇论文
]
```

### 实际对话示例

```
用户：我想了解 Attention Is All You Need 这篇论文

Claude：我来帮你获取和分析这篇论文。

[调用 get_paper_info]
标题：Attention Is All You Need
作者：Ashish Vaswani, Noam Shazeer, et al.
发布日期：2017-06-12

[调用 analyze_paper]
中文摘要：本文提出了一种新的简单网络架构——Transformer，
完全基于注意力机制，摒弃了循环和卷积结构...

主要创新点：
1. 提出了 Transformer 架构
2. 引入了多头注意力机制
3. 使用位置编码

关键词：transformer, attention, neural network, NLP

用户：太棒了，帮我下载这篇论文并生成问答对

Claude：好的，我来下载论文并生成问答对。

[调用 download_paper]
✓ 论文已下载到 output/pdfs/1706.03762.pdf

[调用 analyze_paper，analysis_types=["qa_pairs"]]
✓ 生成了5个问答对：

Q1: Transformer 架构的核心创新是什么？
A1: Transformer 的核心创新是完全使用注意力机制...

Q2: 多头注意力的作用是什么？
A2: 多头注意力允许模型同时关注来自不同位置的信息...

...
```

---

## 故障排查

### 问题 1：MCP 连接失败

**症状：**
```
claude mcp list
arxiv-parser: ... - ✗ Failed to connect
```

**解决方案：**

1. **检查 Python 路径**
   ```bash
   # 确保使用 conda 环境的 Python
   conda activate arxiv_parser
   which python3
   # 应该是：/path/to/conda/env/bin/python3
   
   # 而不是系统 Python
   /usr/bin/python3  # ❌ 错误
   ```

2. **检查配置文件**
   ```bash
   # 查看 .mcp.json
   cat .mcp.json
   
   # 确保 command 是完整路径
   {
     "command": "/home/user/miniconda3/envs/arxiv_parser/bin/python3"
   }
   ```

3. **手动测试 MCP 服务器**
   ```bash
   echo '{"jsonrpc":"2.0","id":1,"method":"tools/list","params":{}}' | \
     /home/user/miniconda3/envs/arxiv_parser/bin/python3 -m adapters.inbound.mcp_server
   
   # 应该返回工具列表 JSON
   ```

4. **重启 Claude Code**
   ```bash
   exit  # 退出 Claude Code
   claude  # 重新启动
   ```

### 问题 2：analyze_paper 工具失败

**症状：**
```
分析论文失败：DEEPSEEK_API_KEY 未配置
```

**解决方案：**

1. **检查 .env 文件**
   ```bash
   cat .env
   # 应该有：DEEPSEEK_API_KEY=sk-xxx
   ```

2. **验证 API Key**
   ```bash
   python -c "from dotenv import load_dotenv; load_dotenv(); import os; print(os.getenv('DEEPSEEK_API_KEY')[:10] + '...')"
   ```

3. **检查依赖**
   ```bash
   pip list | grep -E "requests|mcp"
   # 应该看到 requests 和 mcp
   ```

### 问题 3：搜索返回不相关结果

**症状：** 搜索 "RAG" 但返回的是最新论文而不是相关论文

**原因：** arxiv API 默认按日期排序

**解决方案：**
```python
# 在 fetcher.py 中修改排序方式
search = arxiv.Search(
    query=query,
    max_results=max_results,
    sort_by=arxiv.SortCriterion.Relevance  # 按相关性排序
)
```

### 问题 4：模块导入错误

**症状：**
```
ModuleNotFoundError: No module named 'arxiv_parser'
```

**解决方案：**

1. **设置 PYTHONPATH**
   ```bash
   export PYTHONPATH=/path/to/arxiv_parser:$PYTHONPATH
   ```

2. **或在 .mcp.json 中添加环境变量**
   ```json
   {
     "env": {
       "PYTHONPATH": "/path/to/arxiv_parser"
     }
   }
   ```

3. **确保在项目根目录运行**
   ```bash
   cd /path/to/arxiv_parser
   ```

---

## 高级配置

### 多 MCP 服务器

如果你想同时使用多个 MCP 服务器：

```json
{
  "mcpServers": {
    "arxiv-parser": {
      "command": "/path/to/python3",
      "args": ["-m", "adapters.inbound.mcp_server"]
    },
    "other-tool": {
      "command": "/path/to/other/server",
      "args": ["..."]
    }
  }
}
```

### 自定义分析参数

编辑 `config/config.yaml`：

```yaml
llm:
  provider: "deepseek"
  model: "deepseek-chat"
  temperature: 0.3
  max_tokens: 2000

output:
  language: "both"  # zh / en / both
  include_qa: true
  qa_count: 5
```

### 日志调试

启用详细日志：

```bash
# 设置日志级别
export LOGURU_LEVEL=DEBUG

# 查看日志
tail -f logs/mcp_server.log
```

### 性能优化

**批量分析时：**

```python
# 在 analyzer.py 中调整批处理大小
batch_size = 5  # 每次处理5篇论文

# 添加延迟避免 API 限流
time.sleep(1)  # 每次调用间隔1秒
```

---

## 参考资源

- [MCP 协议官方文档](https://modelcontextprotocol.io)
- [Claude Code MCP 配置指南](https://docs.anthropic.com/claude-code/mcp)
- [arxiv.py 文档](https://github.com/lukasschwab/arxiv.py)
- [DeepSeek API 文档](https://platform.deepseek.com/api-docs)

---

## 常见问题 (FAQ)

**Q: MCP 服务器可以同时被多个 AI 助手使用吗？**

A: 可以。MCP 是标准协议，任何支持 MCP 的 AI 助手都可以连接。

**Q: 分析一篇论文需要多长时间？**

A: 取决于论文长度和分析类型。通常：
- 下载：5-10秒
- 解析：2-5秒
- LLM 分析：10-30秒
- 总计：约 20-45秒

**Q: 可以离线使用吗？**

A: 部分可以。搜索和下载需要网络，但已下载的论文可以在本地解析。LLM 分析需要调用 API。

**Q: 如何更新 MCP 工具？**

A: 修改 `adapters/inbound/mcp_server.py`，使用 `@mcp.tool()` 装饰器添加新工具后重启 Claude Code。

**Q: 支持哪些 LLM 提供商？**

A: 当前支持 DeepSeek（远程 API）和 Ollama（本地模型）。

---

## 贡献

欢迎提交 Issue 和 Pull Request！

**更新日志：**
- 2026-11-09: 添加 analyze_paper 工具，支持 LLM 智能分析
- 2026-11-09: 修复 MCP 协议 initialize 方法
- 2026-11-09: 初始 MCP 集成
