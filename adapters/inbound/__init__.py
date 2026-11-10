"""
Inbound Adapters - 本系统被外部调用
"""

from .mcp_server import mcp, main

__all__ = [
    "mcp",
    "main",
]
