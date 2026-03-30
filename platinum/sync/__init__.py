"""
Vault Sync Package

Shared synchronization utilities for Cloud and Local agents.
Implements Git-based vault sync with:
- Conflict detection and resolution
- Encryption support (optional)
- Claim-by-move rule enforcement
"""

from .vault_sync import VaultSync, SyncResult
from .conflict_resolver import ConflictResolver
from .encryption import VaultEncryption

__all__ = ["VaultSync", "SyncResult", "ConflictResolver", "VaultEncryption"]
