"""
Local Agent Package

Platinum Tier: Always-On Cloud + Local Executive

Local Agent runs on your local machine and handles:
- Human approval workflows
- Executing sensitive actions (send email, post social, payments)
- WhatsApp session management
- Banking credentials (never synced to cloud)
- Final "send/post" actions via MCP
"""

from .config import LocalConfig, get_config, init_config

__all__ = ["LocalConfig", "get_config", "init_config"]
