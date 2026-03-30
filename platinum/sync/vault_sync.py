"""
Vault Sync Core

Core Git-based vault synchronization implementation.
Used by both Cloud and Local agents.
"""

import logging
import subprocess
import os
from pathlib import Path
from datetime import datetime
from typing import Optional, List, Dict, Tuple
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class SyncResult:
    """Result of a sync operation"""
    success: bool
    status: str  # synced, conflicted, error, diverged
    uncommitted_changes: int = 0
    unpushed_commits: int = 0
    unpulled_commits: int = 0
    conflicts: List[str] = None
    last_pull: Optional[datetime] = None
    last_push: Optional[datetime] = None
    error_message: Optional[str] = None
    
    def __post_init__(self):
        if self.conflicts is None:
            self.conflicts = []


class VaultSync:
    """
    Vault Sync Core
    
    Handles Git-based synchronization between Cloud and Local.
    """
    
    def __init__(
        self,
        vault_path: Path,
        git_remote: str,
        git_branch: str = "main",
        agent_type: str = "cloud",  # cloud or local
    ):
        self.vault_path = vault_path.resolve()
        self.git_remote = git_remote
        self.git_branch = git_branch
        self.agent_type = agent_type
        
        # Sync tracking
        self.last_pull: Optional[datetime] = None
        self.last_push: Optional[datetime] = None
        self.sync_count: int = 0
        
        # Ensure vault path exists
        self.vault_path.mkdir(parents=True, exist_ok=True)
        
        # Setup gitignore
        self._ensure_gitignore()
    
    def _ensure_gitignore(self):
        """Ensure .gitignore properly excludes secrets"""
        gitignore_path = self.vault_path / ".gitignore"
        
        # Patterns that should never sync
        secrets_patterns = [
            "# Secrets - NEVER SYNC",
            ".env",
            "*.env",
            "credentials.json",
            "token.json",
            "tokens.json",
            ".secrets/",
            "whatsapp_session/",
            "session/",
            "*.session",
            "# Local state",
            ".git/",
            "# Logs (JSONL not synced)",
            "Logs/*.jsonl",
            "Audit/json/*.jsonl",
            "# Cache",
            "__pycache__/",
            "*.pyc",
            "node_modules/",
        ]
        
        if not gitignore_path.exists():
            gitignore_path.write_text("\n".join(secrets_patterns), encoding='utf-8')
            logger.info(f"Created .gitignore at {gitignore_path}")
        else:
            # Verify all patterns are present
            content = gitignore_path.read_text(encoding='utf-8')
            missing = []
            
            for pattern in secrets_patterns:
                if not pattern.startswith('#') and pattern not in content:
                    missing.append(pattern)
            
            if missing:
                with open(gitignore_path, 'a', encoding='utf-8') as f:
                    f.write("\n# Added by VaultSync\n")
                    for pattern in missing:
                        f.write(f"{pattern}\n")
                logger.info(f"Added {len(missing)} missing patterns to .gitignore")
    
    def initialize(self) -> bool:
        """Initialize Git repository"""
        git_dir = self.vault_path / ".git"
        
        if git_dir.exists():
            logger.info("Git repository already exists")
            return True
        
        try:
            self._git("init")
            self._git("branch", "-M", self.git_branch)
            self._git("add", ".")
            self._git("commit", "-m", "Initial commit - Vault setup")
            
            logger.info("Git repository initialized")
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize Git: {e}")
            return False
    
    def configure_remote(self, remote_url: str) -> bool:
        """Configure Git remote"""
        try:
            try:
                self._git("remote", "remove", "origin")
            except:
                pass
            
            self._git("remote", "add", "origin", remote_url)
            logger.info(f"Configured remote: {remote_url}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to configure remote: {e}")
            return False
    
    def sync(self) -> SyncResult:
        """Perform full sync (pull → process → push)"""
        logger.info("Starting sync...")
        
        # Pull
        pull_result = self.pull()
        if pull_result.status == "conflicted":
            return pull_result
        
        # Push
        push_result = self.push()
        
        return push_result
    
    def pull(self) -> SyncResult:
        """Pull changes from remote"""
        result = SyncResult(success=False, status="unknown")
        
        try:
            # Fetch
            self._git("fetch", "origin")
            
            # Check conflicts
            conflicts = self._check_conflicts()
            if conflicts:
                result.status = "conflicted"
                result.conflicts = conflicts
                return result
            
            # Pull
            self._git("pull", "origin", self.git_branch)
            
            self.last_pull = datetime.now()
            self.sync_count += 1
            
            result.success = True
            result.status = "synced"
            result.last_pull = self.last_pull
            
            logger.info(f"Pulled from remote (sync #{self.sync_count})")
            
        except Exception as e:
            result.status = "error"
            result.error_message = str(e)
            logger.error(f"Pull failed: {e}")
        
        return result
    
    def push(self) -> SyncResult:
        """Push changes to remote"""
        result = SyncResult(success=False, status="unknown")
        
        try:
            # Stage
            self._git("add", ".")
            
            # Check for changes
            status_output = self._git("status", "--porcelain")
            changes = [l for l in status_output.split('\n') if l.strip()]
            result.uncommitted_changes = len(changes)
            
            if not changes:
                result.success = True
                result.status = "synced"
                return result
            
            # Commit
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            agent = self.agent_type.capitalize()
            self._git("commit", "-m", f"{agent} Agent update - {timestamp}")
            
            # Check unpushed commits
            unpushed = self._git("rev-list", "--count", "HEAD..origin/" + self.git_branch)
            result.unpushed_commits = int(unpushed.strip()) if unpushed.strip() else 0
            
            # Push
            self._git("push", "origin", self.git_branch)
            
            self.last_push = datetime.now()
            self.sync_count += 1
            
            result.success = True
            result.status = "synced"
            result.last_push = self.last_push
            
            logger.info(f"Pushed to remote (sync #{self.sync_count})")
            
        except Exception as e:
            result.status = "error"
            result.error_message = str(e)
            logger.error(f"Push failed: {e}")
        
        return result
    
    def _check_conflicts(self) -> List[str]:
        """Check for merge conflicts"""
        try:
            output = self._git("diff", "--name-only", "--diff-filter=U")
            if output.strip():
                return [line.strip() for line in output.split('\n') if line.strip()]
        except:
            pass
        return []
    
    def _git(self, *args, timeout: int = 30) -> str:
        """Run Git command"""
        cmd = ["git"] + list(args)
        
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            cwd=str(self.vault_path),
            timeout=timeout,
            env={**os.environ, "GIT_TERMINAL_PROMPT": "0"}
        )
        
        if result.returncode != 0:
            raise subprocess.CalledProcessError(
                result.returncode, cmd, result.stdout, result.stderr
            )
        
        return result.stdout.strip()
    
    def get_status(self) -> SyncResult:
        """Get current sync status"""
        result = SyncResult(success=True, status="unknown")
        
        try:
            # Uncommitted changes
            output = self._git("status", "--porcelain")
            result.uncommitted_changes = len([l for l in output.split('\n') if l.strip()])
            
            # Unpushed commits
            unpushed = self._git("rev-list", "--count", "HEAD..origin/" + self.git_branch)
            result.unpushed_commits = int(unpushed.strip()) if unpushed.strip() else 0
            
            # Unpulled commits
            unpulled = self._git("rev-list", "--count", "origin/" + self.git_branch + "..HEAD")
            result.unpulled_commits = int(unpulled.strip()) if unpulled.strip() else 0
            
            # Determine status
            if result.unpushed_commits > 0 and result.unpulled_commits > 0:
                result.status = "diverged"
            elif result.unpushed_commits > 0:
                result.status = "ahead"
            elif result.unpulled_commits > 0:
                result.status = "behind"
            elif result.uncommitted_changes > 0:
                result.status = "modified"
            else:
                result.status = "synced"
            
        except Exception as e:
            result.status = "error"
            result.error_message = str(e)
        
        return result


def create_vault_sync(
    vault_path: str,
    git_remote: str,
    git_branch: str = "main",
    agent_type: str = "cloud"
) -> VaultSync:
    """Create VaultSync instance"""
    return VaultSync(
        vault_path=Path(vault_path),
        git_remote=git_remote,
        git_branch=git_branch,
        agent_type=agent_type,
    )


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    # Test vault sync
    sync = create_vault_sync(
        vault_path="./test_vault",
        git_remote="https://github.com/example/test.git",
        agent_type="cloud",
    )
    
    if sync.initialize():
        status = sync.get_status()
        logger.info(f"Status: {status.status}")
