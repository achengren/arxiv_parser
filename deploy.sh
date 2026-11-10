#!/bin/bash
# arXiv Parser 环境搭建/部署脚本（唯一 setup 入口）
# 优先用 conda 建隔离环境，没有 conda 则回退到系统 pip。
# 依赖统一由 pyproject.toml 管理，这里只负责装（含 MCP）。

set -euo pipefail

cd "$(dirname "$0")"

echo "=========================================="
echo "  arXiv Parser 环境搭建"
echo "=========================================="

if command -v conda &> /dev/null; then
    echo "✓ 检测到 conda: $(command -v conda)"

    # 初始化 conda（激活环境需要先 source conda.sh）
    for init in "$HOME/miniconda3/etc/profile.d/conda.sh" "$HOME/anaconda3/etc/profile.d/conda.sh"; do
        if [ -f "$init" ]; then
            source "$init"
            break
        fi
    done

    # 环境不存在才创建，已存在则直接装依赖（幂等）
    if ! conda env list | grep -qE "^arxiv_parser[[:space:]]"; then
        echo "创建 conda 环境 'arxiv_parser'..."
        conda env create -f environment.yml
    else
        echo "环境 'arxiv_parser' 已存在，跳过创建"
    fi

    conda activate arxiv_parser
    python -m pip install --upgrade pip
    python -m pip install -e ".[mcp]"
else
    echo "未检测到 conda，回退到系统 pip"
    pip3 install --upgrade pip
    pip3 install -e ".[mcp]"
fi

echo ""
echo "=========================================="
echo "  ✓ 环境搭建完成"
echo "=========================================="
echo ""
echo "下一步："
echo "  1. 配置 .env：cp .env.example .env 并填入 DEEPSEEK_API_KEY"
echo "  2. 健康检查：python3 quickstart.py"
echo "  3. 运行：python -m arxiv_parser --help"
