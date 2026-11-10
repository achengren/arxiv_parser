#!/usr/bin/env bash
# MCP 启动包装脚本：定位 arxiv_parser 的 Python 解释器并启动 server。
# 优先级：.env 的 ARXIV_PARSER_PYTHON > 标准 conda 目录自动探测 > 系统 python3。
# 换机器部署时只需改 .env 里的 ARXIV_PARSER_PYTHON（或不改，自动探测）。
set -euo pipefail

cd "$(dirname "$0")"

# 加载 .env（同时把 DEEPSEEK_API_KEY 等变量导出给 Python 进程）
if [ -f .env ]; then
  set -a
  # shellcheck disable=SC1091
  . ./.env
  set +a
fi

# 1) 显式指定的解释器
if [ -n "${ARXIV_PARSER_PYTHON:-}" ] && [ -x "$ARXIV_PARSER_PYTHON" ]; then
  exec "$ARXIV_PARSER_PYTHON" -m adapters.inbound.mcp_server "$@"
fi

# 2) 常见 conda 目录自动探测
for p in \
  "$HOME/miniconda3/envs/arxiv_parser/bin/python3" \
  "$HOME/anaconda3/envs/arxiv_parser/bin/python3" \
  "$HOME/miniconda3/envs/arxiv_parser/bin/python" \
  "$HOME/anaconda3/envs/arxiv_parser/bin/python"; do
  if [ -x "$p" ]; then
    exec "$p" -m adapters.inbound.mcp_server "$@"
  fi
done

# 3) 兜底：系统 python3
exec python3 -m adapters.inbound.mcp_server "$@"
