"""
Local Agent Configuration

Local Agent runs on your personal machine and handles:
- Human-in-the-loop approvals
- Executing sensitive actions via MCP
- WhatsApp session management
- Banking/payment credentials
- Final send/post actions

Security: Secrets NEVER leave this machine (never sync to cloud)
"""

import os
from pathlib import Path
from typing import Optional
from dataclasses import dataclass, field


@dataclass
class LocalConfig:
    """Local Agent configuration"""
    
    # Agent identity
    agent_id: str = "local_agent"
    agent_name: str = "Local Executive"
    
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
    whatsapp_session_dir: Path = field(default_factory=lambda: Path(os.getenv("WHATSAPP_SESSION_PATH", "whatsapp_session")))
    
    # Git sync configuration
    git_remote: str = os.getenv("GIT_REMOTE", "")
    git_branch: str = os.getenv("GIT_BRANCH", "main")
    sync_interval: int = int(os.getenv("SYNC_INTERVAL", "60"))  # seconds
    
    # Approval configuration
    auto_approve_threshold: float = float(os.getenv("AUTO_APPROVE_THRESHOLD", "0"))  # Never auto-approve
    approval_timeout_hours: int = int(os.getenv("APPROVAL_TIMEOUT_HOURS", "24"))
    max_pending_approvals: int = int(os.getenv("MAX_PENDING_APPROVALS", "100"))
    
    # MCP configuration
    mcp_timeout: int = int(os.getenv("MCP_TIMEOUT", "60"))  # seconds
    mcp_max_retries: int = int(os.getenv("MCP_MAX_RETRIES", "3"))
    
    # Rate limiting (Local is more permissive since it has credentials)
    max_emails_per_hour: int = int(os.getenv("MAX_EMAILS_PER_HOUR", "20"))
    max_social_posts_per_day: int = int(os.getenv("MAX_SOCIAL_POSTS_PER_DAY", "50"))
    max_payments_per_day: int = int(os.getenv("MAX_PAYMENTS_PER_DAY", "10"))
    max_payment_amount: float = float(os.getenv("MAX_PAYMENT_AMOUNT", "1000.0"))
    
    # Notification configuration
    desktop_notifications: bool = os.getenv("DESKTOP_NOTIFICATIONS", "true").lower() == "true"
    notification_sound: bool = os.getenv("NOTIFICATION_SOUND", "true").lower() == "true"
    email_notifications: bool = os.getenv("EMAIL_NOTIFICATIONS", "false").lower() == "true"
    notification_email: str = os.getenv("NOTIFICATION_EMAIL", "")
    
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
    
    # Security
    require_approval_for_new_contacts: bool = os.getenv("REQUIRE_APPROVAL_NEW_CONTACTS", "true").lower() == "true"
    require_approval_for_payments: bool = os.getenv("REQUIRE_APPROVAL_PAYMENTS", "true").lower() == "true"
    dry_run: bool = os.getenv("DRY_RUN", "true").lower() == "true"
    
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
    def full_approved_path(self) -> Path:
        """Get absolute Approved path"""
        return self.full_vault_path / self.approved_dir
    
    @property
    def full_done_path(self) -> Path:
        """Get absolute Done path"""
        return self.full_vault_path / self.done_dir
    
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
        """Get absolute secrets path (local only, NEVER sync)"""
        return self.full_vault_path / self.secrets_dir
    
    @property
    def full_whatsapp_session_path(self) -> Path:
        """Get absolute WhatsApp session path (local only)"""
        return self.full_vault_path / self.whatsapp_session_dir
    
    @property
    def full_plans_path(self) -> Path:
        return self.full_vault_path / self.plans_dir
    
    @property
    def full_log_path(self) -> Path:
        return self.full_vault_path / self.log_dir
    
    @property
    def full_audit_path(self) -> Path:
        return self.full_vault_path / self.audit_dir
    
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
            self.full_secrets_path,  # Local only
            self.full_whatsapp_session_path,  # Local only
        ]
        for d in dirs:
            d.mkdir(parents=True, exist_ok=True)
        
        # Create .gitignore in secrets directory
        gitignore = self.full_secrets_path / ".gitignore"
        gitignore.write_text("*\n# Never sync any secrets", encoding='utf-8')
    
    def is_payment_approved(self, amount: float) -> bool:
        """Check if payment amount is within limits"""
        if amount > self.max_payment_amount:
            return False
        return True
    
    def requires_approval(self, action_type: str, metadata: dict) -> bool:
        """
        Determine if action requires human approval
        
        Rules:
        - All payments require approval
        - All social posts require approval
        - All emails to new contacts require approval
        - All actions over threshold require approval
        """
        # Payment always requires approval
        if action_type in ["payment", "invoice_post"]:
            return self.require_approval_for_payments
        
        # Social posts always require approval
        if action_type in ["social_post", "tweet", "facebook_post", "instagram_post"]:
            return True
        
        # Email to new contact requires approval
        if action_type == "email_send":
            if self.require_approval_for_new_contacts:
                return True  # Conservative: always approve emails
        
        # Check amount threshold
        amount = metadata.get("amount", 0)
        if amount > float(self.auto_approve_threshold):
            return True
        
        return True
    
    def to_env_dict(self) -> dict:
        """Export config as environment variables dict"""
        return {
            "VAULT_PATH": str(self.vault_path),
            "AGENT_ID": self.agent_id,
            "GIT_REMOTE": self.git_remote,
            "GIT_BRANCH": self.git_branch,
            "SYNC_INTERVAL": str(self.sync_interval),
            "DRY_RUN": str(self.dry_run),
            "LOG_LEVEL": self.log_level,
        }


# Global config instance
_config: Optional[LocalConfig] = None


def get_config() -> LocalConfig:
    """Get or create global config instance"""
    global _config
    if _config is None:
        _config = LocalConfig()
        _config.ensure_directories()
    return _config


def init_config(
    git_remote: str,
    git_branch: str = "main",
    agent_id: str = "local_agent",
    vault_path: str = "./AI_Employee_Vault",
    **kwargs
) -> LocalConfig:
    """Initialize config with custom values"""
    global _config
    _config = LocalConfig(
        agent_id=agent_id,
        vault_path=Path(vault_path),
        git_remote=git_remote,
        git_branch=git_branch,
        **kwargs
    )
    _config.ensure_directories()
    return _config
