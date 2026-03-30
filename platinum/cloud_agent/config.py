"""
Cloud Agent Configuration

This module handles configuration for the Cloud Agent running on a 24/7 VM.
Cloud Agent is responsible for:
- Email triage and draft replies
- Social media monitoring and draft posts
- Lead capture
- Draft-only actions (requires Local approval for execution)
"""

import os
from pathlib import Path
from typing import Optional
from dataclasses import dataclass, field


@dataclass
class CloudConfig:
    """Cloud Agent configuration"""
    
    # Agent identity
    agent_id: str = "cloud_agent"
    agent_name: str = "Cloud Executive"
    
    # Vault paths (synced via Git)
    vault_path: Path = field(default_factory=lambda: Path(os.getenv("VAULT_PATH", "./AI_Employee_Vault")))
    
    # Synced directories
    inbox_dir: Path = field(default_factory=lambda: Path(os.getenv("INBOX_PATH", "Inbox")))
    needs_action_dir: Path = field(default_factory=lambda: Path(os.getenv("NEEDS_ACTION_PATH", "Needs_Action")))
    plans_dir: Path = field(default_factory=lambda: Path(os.getenv("PLANS_PATH", "Plans")))
    pending_approval_dir: Path = field(default_factory=lambda: Path(os.getenv("PENDING_APPROVAL_PATH", "Pending_Approval")))
    approved_dir: Path = field(default_factory=lambda: Path(os.getenv("APPROVED_PATH", "Approved")))
    done_dir: Path = field(default_factory=lambda: Path(os.getenv("DONE_PATH", "Done")))
    in_progress_dir: Path = field(default_factory=lambda: Path(os.getenv("IN_PROGRESS_PATH", "In_Progress")))
    updates_dir: Path = field(default_factory=lambda: Path(os.getenv("UPDATES_PATH", "Updates")))
    signals_dir: Path = field(default_factory=lambda: Path(os.getenv("SIGNALS_PATH", "Signals")))
    
    # Local-only directories (NEVER sync)
    secrets_dir: Path = field(default_factory=lambda: Path(os.getenv("SECRETS_PATH", ".secrets")))
    
    # Git sync configuration
    git_remote: str = os.getenv("GIT_REMOTE", "")
    git_branch: str = os.getenv("GIT_BRANCH", "main")
    sync_interval: int = int(os.getenv("SYNC_INTERVAL", "60"))  # seconds
    
    # Watcher configuration
    gmail_check_interval: int = int(os.getenv("GMAIL_CHECK_INTERVAL", "120"))
    social_check_interval: int = int(os.getenv("SOCIAL_CHECK_INTERVAL", "300"))
    lead_check_interval: int = int(os.getenv("LEAD_CHECK_INTERVAL", "300"))
    
    # Draft configuration
    max_drafts_pending: int = int(os.getenv("MAX_DRAFTS_PENDING", "50"))
    draft_expiry_hours: int = int(os.getenv("DRAFT_EXPIRY_HOURS", "24"))
    
    # Rate limiting (Cloud is more conservative)
    max_emails_per_hour: int = int(os.getenv("MAX_EMAILS_PER_HOUR", "5"))
    max_social_posts_per_day: int = int(os.getenv("MAX_SOCIAL_POSTS_PER_DAY", "10"))
    max_api_calls_per_minute: int = int(os.getenv("MAX_API_CALLS_PER_MINUTE", "10"))
    
    # Error handling
    max_retries: int = int(os.getenv("MAX_RETRIES", "3"))
    retry_base_delay: int = int(os.getenv("RETRY_BASE_DELAY", "5"))
    circuit_breaker_threshold: int = int(os.getenv("CIRCUIT_BREAKER_THRESHOLD", "3"))
    circuit_breaker_timeout: int = int(os.getenv("CIRCUIT_BREAKER_TIMEOUT", "300"))
    
    # Logging
    log_level: str = os.getenv("LOG_LEVEL", "INFO")
    log_dir: Path = field(default_factory=lambda: Path(os.getenv("LOG_PATH", "Logs")))
    audit_dir: Path = field(default_factory=lambda: Path(os.getenv("AUDIT_PATH", "Audit/json")))
    
    # Health check
    health_check_interval: int = int(os.getenv("HEALTH_CHECK_INTERVAL", "30"))
    watchdog_timeout: int = int(os.getenv("WATCHDOG_TIMEOUT", "300"))
    
    # Cloud-specific settings
    cloud_provider: str = os.getenv("CLOUD_PROVIDER", "oracle")
    vm_region: str = os.getenv("VM_REGION", "us-ashburn-1")
    https_enabled: bool = os.getenv("HTTPS_ENABLED", "true").lower() == "true"
    
    @property
    def full_vault_path(self) -> Path:
        """Get absolute vault path"""
        return self.vault_path.resolve()
    
    @property
    def full_needs_action_path(self) -> Path:
        """Get absolute Needs_Action path"""
        return self.full_vault_path / self.needs_action_dir
    
    @property
    def full_pending_approval_path(self) -> Path:
        """Get absolute Pending_Approval path"""
        return self.full_vault_path / self.pending_approval_dir
    
    @property
    def full_in_progress_path(self) -> Path:
        """Get absolute In_Progress path"""
        return self.full_vault_path / self.in_progress_dir
    
    @property
    def full_updates_path(self) -> Path:
        """Get absolute Updates path"""
        return self.full_vault_path / self.updates_dir
    
    @property
    def full_signals_path(self) -> Path:
        """Get absolute Signals path"""
        return self.full_vault_path / self.signals_dir
    
    @property
    def full_secrets_path(self) -> Path:
        """Get absolute secrets path (local only)"""
        return self.full_vault_path / self.secrets_dir
    
    def ensure_directories(self):
        """Create all required directories"""
        dirs = [
            self.full_vault_path,
            self.full_needs_action_path,
            self.full_plans_path,
            self.full_pending_approval_path,
            self.full_approved_path,
            self.full_done_path,
            self.full_in_progress_path,
            self.full_updates_path,
            self.full_signals_path,
            self.full_log_path,
            self.full_audit_path,
        ]
        for d in dirs:
            d.mkdir(parents=True, exist_ok=True)
    
    @property
    def full_plans_path(self) -> Path:
        return self.full_vault_path / self.plans_dir
    
    @property
    def full_approved_path(self) -> Path:
        return self.full_vault_path / self.approved_dir
    
    @property
    def full_done_path(self) -> Path:
        return self.full_vault_path / self.done_dir
    
    @property
    def full_log_path(self) -> Path:
        return self.full_vault_path / self.log_dir
    
    @property
    def full_audit_path(self) -> Path:
        return self.full_vault_path / self.audit_dir
    
    def to_env_dict(self) -> dict:
        """Export config as environment variables dict"""
        return {
            "VAULT_PATH": str(self.vault_path),
            "AGENT_ID": self.agent_id,
            "GIT_REMOTE": self.git_remote,
            "GIT_BRANCH": self.git_branch,
            "SYNC_INTERVAL": str(self.sync_interval),
            "GMAIL_CHECK_INTERVAL": str(self.gmail_check_interval),
            "SOCIAL_CHECK_INTERVAL": str(self.social_check_interval),
            "LOG_LEVEL": self.log_level,
        }


# Global config instance
_config: Optional[CloudConfig] = None


def get_config() -> CloudConfig:
    """Get or create global config instance"""
    global _config
    if _config is None:
        _config = CloudConfig()
        _config.ensure_directories()
    return _config


def init_config(
    git_remote: str,
    git_branch: str = "main",
    agent_id: str = "cloud_agent",
    vault_path: str = "./AI_Employee_Vault",
    **kwargs
) -> CloudConfig:
    """Initialize config with custom values"""
    global _config
    _config = CloudConfig(
        agent_id=agent_id,
        vault_path=Path(vault_path),
        git_remote=git_remote,
        git_branch=git_branch,
        **kwargs
    )
    _config.ensure_directories()
    return _config
