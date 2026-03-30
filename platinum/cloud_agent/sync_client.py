"""
Cloud Sync Client

Handles Git-based vault synchronization between Cloud and Local agents.
Implements:
- Git push/pull for vault sync
- Claim-by-move rule enforcement
- Conflict detection
- Secrets exclusion (never sync .env, tokens, credentials)
"""

import logging
import subprocess
import os
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass

from .config import CloudConfig, get_config

logger = logging.getLogger(__name__)


@dataclass
class SyncStatus:
    """Git sync status"""
    last_pull: Optional[datetime] = None
    last_push: Optional[datetime] = None
    uncommitted_changes: int = 0
    unpushed_commits: int = 0
    unpulled_commits: int = 0
    conflicts: List[str] = None
    status: str = "unknown"  # synced, behind, ahead, conflicted
    
    def __post_init__(self):
        if self.conflicts is None:
            self.conflicts = []


class CloudSyncClient:
    """
    Cloud Sync Client
    
    Manages Git-based vault synchronization:
    - Pull changes from Local (approvals, completions)
    - Push changes to Local (drafts, action files)
    - Handle conflicts gracefully
    - Never sync secrets
    """
    
    def __init__(self, config: Optional[CloudConfig] = None):
        self.config = config or get_config()
        self.vault_path = self.config.full_vault_path
        self.git_remote = self.config.git_remote
        self.git_branch = self.config.git_branch
        
        # Sync tracking
        self.last_pull: Optional[datetime] = None
        self.last_push: Optional[datetime] = None
        self.sync_count: int = 0
        
        # Ensure .gitignore is properly configured
        self._ensure_gitignore()
    
    def _ensure_gitignore(self):
        """Ensure .gitignore excludes secrets"""
        gitignore_path = self.vault_path / ".gitignore"
        
        secrets_patterns = [
            "# Secrets - NEVER SYNC",
            ".env",
            "*.env",
            "credentials.json",
            "token.json",
            "tokens.json",
            ".secrets/",
            "session/",
            "*.session",
            "# Local state",
            ".git/",
            "# Logs (sync only summaries)",
            "Logs/*.jsonl",
            "Audit/json/*.jsonl",
            "# PM2 logs",
            "pm2/",
            "# Python cache",
            "__pycache__/",
            "*.pyc",
            ".python-version",
            "# Node modules",
            "node_modules/",
        ]
        
        if not gitignore_path.exists():
            gitignore_path.write_text("\n".join(secrets_patterns), encoding='utf-8')
            logger.info(f"Created .gitignore at {gitignore_path}")
        else:
            # Verify secrets are excluded
            content = gitignore_path.read_text(encoding='utf-8')
            missing = [p for p in secrets_patterns if p not in content and not p.startswith('#')]
            
            if missing:
                # Append missing patterns
                with open(gitignore_path, 'a', encoding='utf-8') as f:
                    f.write("\n# Added by Cloud Sync\n")
                    for pattern in missing:
                        f.write(f"{pattern}\n")
                logger.info(f"Updated .gitignore with {len(missing)} patterns")
    
    def initialize_git(self) -> bool:
        """Initialize Git repository if not exists"""
        git_dir = self.vault_path / ".git"
        
        if git_dir.exists():
            logger.info("Git repository already initialized")
            return True
        
        try:
            # Initialize git repo
            self._run_git_command("init")
            
            # Set default branch
            self._run_git_command("branch", "-M", self.git_branch)
            
            # Create initial commit
            self._run_git_command("add", ".")
            self._run_git_command("commit", "-m", "Initial commit - Cloud Agent setup")
            
            logger.info("Git repository initialized")
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize Git: {e}")
            return False
    
    def configure_remote(self, remote_url: str) -> bool:
        """Configure Git remote"""
        try:
            # Remove existing remote if any
            try:
                self._run_git_command("remote", "remove", "origin")
            except:
                pass
            
            # Add new remote
            self._run_git_command("remote", "add", "origin", remote_url)
            
            self.git_remote = remote_url
            logger.info(f"Configured Git remote: {remote_url}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to configure remote: {e}")
            return False
    
    def pull_changes(self) -> SyncStatus:
        """
        Pull changes from remote (Local Agent pushes)
        
        Returns sync status with any conflicts
        """
        status = SyncStatus()
        
        try:
            # Fetch remote changes
            self._run_git_command("fetch", "origin")
            
            # Check for conflicts before merge
            conflicts = self._check_conflicts()
            if conflicts:
                status.conflicts = conflicts
                status.status = "conflicted"
                logger.warning(f"Conflicts detected: {conflicts}")
                return status
            
            # Pull changes
            self._run_git_command("pull", "origin", self.git_branch)
            
            self.last_pull = datetime.now()
            self.sync_count += 1
            
            status.last_pull = self.last_pull
            status.status = "synced"
            
            logger.info(f"Pulled changes from remote (sync #{self.sync_count})")
            
        except subprocess.CalledProcessError as e:
            logger.error(f"Git pull failed: {e}")
            status.status = "error"
        except Exception as e:
            logger.error(f"Pull error: {e}")
            status.status = "error"
        
        return status
    
    def push_changes(self) -> SyncStatus:
        """
        Push changes to remote (Local Agent pulls)
        
        Commits all pending changes and pushes
        """
        status = SyncStatus()
        
        try:
            # Stage all changes
            self._run_git_command("add", ".")
            
            # Check if there are changes to commit
            result = self._run_git_command("status", "--porcelain")
            if not result.strip():
                status.status = "synced"
                logger.info("No changes to push")
                return status
            
            # Count changes
            status.uncommitted_changes = len([l for l in result.split('\n') if l.strip()])
            
            # Commit changes
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            self._run_git_command(
                "commit",
                "-m", f"Cloud Agent update - {timestamp}"
            )
            
            # Push changes
            self._run_git_command("push", "origin", self.git_branch)
            
            self.last_push = datetime.now()
            self.sync_count += 1
            
            status.last_push = self.last_push
            status.status = "synced"
            
            logger.info(f"Pushed changes to remote (sync #{self.sync_count})")
            
        except subprocess.CalledProcessError as e:
            logger.error(f"Git push failed: {e}")
            status.status = "error"
        except Exception as e:
            logger.error(f"Push error: {e}")
            status.status = "error"
        
        return status
    
    def sync(self) -> SyncStatus:
        """
        Full sync: pull → process → push
        
        This is the main sync method called periodically
        """
        logger.info("Starting full sync...")
        
        # Step 1: Pull changes from Local
        pull_status = self.pull_changes()
        if pull_status.status == "conflicted":
            logger.error("Cannot sync: conflicts detected")
            return pull_status
        
        # Step 2: Process any new approvals from Local
        # (Local moves files from Pending_Approval to Approved)
        self._process_local_updates()
        
        # Step 3: Push new drafts and action files
        push_status = self.push_changes()
        
        return push_status
    
    def _process_local_updates(self):
        """
        Process updates from Local Agent
        
        - Check /Approved/ for executed actions
        - Check /Done/ for completed items
        - Update internal state
        """
        approved_dir = self.config.full_approved_path
        done_dir = self.config.full_done_path
        
        # Process approved items (Local executed these)
        if approved_dir.exists():
            for item_file in approved_dir.iterdir():
                if item_file.is_file() and item_file.suffix == '.md':
                    self._handle_approved_item(item_file)
        
        # Process done items (Local completed these)
        if done_dir.exists():
            for item_file in done_dir.iterdir():
                if item_file.is_file() and item_file.suffix == '.md':
                    self._handle_done_item(item_file)
    
    def _handle_approved_item(self, filepath: Path):
        """Handle item approved and executed by Local"""
        logger.info(f"Local Agent executed: {filepath.name}")
        # Move to In_Progress/cloud_agent or track completion
        # This prevents Cloud from re-processing
        
    def _handle_done_item(self, filepath: Path):
        """Handle item completed by Local"""
        logger.info(f"Local Agent completed: {filepath.name}")
        # Archive or cleanup as needed
    
    def _check_conflicts(self) -> List[str]:
        """Check for Git conflicts"""
        try:
            result = self._run_git_command("diff", "--name-only", "--diff-filter=U")
            if result.strip():
                return [line.strip() for line in result.split('\n') if line.strip()]
        except:
            pass
        return []
    
    def _run_git_command(self, *args, timeout: int = 30) -> str:
        """Run Git command and return output"""
        cmd = ["git"] + list(args)
        
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            cwd=str(self.vault_path),
            timeout=timeout,
            env={**os.environ, "GIT_TERMINAL_PROMPT": "0"}  # Non-interactive
        )
        
        if result.returncode != 0:
            raise subprocess.CalledProcessError(
                result.returncode, cmd, result.stdout, result.stderr
            )
        
        return result.stdout
    
    def get_status(self) -> SyncStatus:
        """Get current sync status"""
        status = SyncStatus()
        status.last_pull = self.last_pull
        status.last_push = self.last_push
        
        try:
            # Check uncommitted changes
            result = self._run_git_command("status", "--porcelain")
            status.uncommitted_changes = len([l for l in result.split('\n') if l.strip()])
            
            # Check unpushed commits
            result = self._run_git_command("rev-list", "--count", f"HEAD..origin/{self.git_branch}")
            status.unpulled_commits = int(result.strip()) if result.strip() else 0
            
            # Check unpulled commits
            result = self._run_git_command("rev-list", "--count", f"origin/{self.git_branch}..HEAD")
            status.unpushed_commits = int(result.strip()) if result.strip() else 0
            
            # Determine overall status
            if status.unpushed_commits > 0 and status.unpulled_commits > 0:
                status.status = "diverged"
            elif status.unpushed_commits > 0:
                status.status = "ahead"
            elif status.unpulled_commits > 0:
                status.status = "behind"
            elif status.uncommitted_changes > 0:
                status.status = "modified"
            else:
                status.status = "synced"
                
        except Exception as e:
            logger.error(f"Error getting status: {e}")
            status.status = "error"
        
        return status
    
    def claim_file(self, filepath: Path) -> bool:
        """
        Claim a file using claim-by-move rule
        
        Moves file from /Needs_Action/ to /In_Progress/cloud_agent/
        """
        source = filepath
        target_dir = self.config.full_in_progress_path / "cloud_agent"
        target_dir.mkdir(parents=True, exist_ok=True)
        
        target = target_dir / filepath.name
        
        try:
            # Check if already claimed
            if target.exists():
                logger.debug(f"File already claimed: {filepath.name}")
                return False
            
            # Move file
            source.rename(target)
            logger.info(f"Claimed file: {filepath.name}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to claim file: {e}")
            return False
    
    def release_file(self, filepath: Path, destination: str = "Done") -> bool:
        """
        Release a claimed file after processing
        
        Moves file from /In_Progress/cloud_agent/ to /Done/ or /Needs_Action/
        """
        source = filepath
        if destination.lower() == "done":
            target_dir = self.config.full_done_path
        else:
            target_dir = self.config.full_needs_action_path
        
        try:
            target = target_dir / filepath.name
            source.rename(target)
            logger.info(f"Released file to {destination}: {filepath.name}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to release file: {e}")
            return False
    
    def write_update(self, update_type: str, content: str, metadata: Dict = None) -> Path:
        """
        Write update to /Updates/ directory for Local to merge
        
        Cloud writes updates here, Local merges into Dashboard.md
        """
        updates_dir = self.config.full_updates_path
        updates_dir.mkdir(parents=True, exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{update_type}_{timestamp}.md"
        filepath = updates_dir / filename
        
        full_content = f"""---
type: {update_type}
timestamp: {datetime.now().isoformat()}
source: cloud_agent
---

{content}
"""
        
        if metadata:
            for key, value in metadata.items():
                full_content = full_content.replace(
                    "source: cloud_agent",
                    f"source: cloud_agent\n{key}: {value}"
                )
        
        filepath.write_text(full_content, encoding='utf-8')
        logger.info(f"Wrote update: {filepath}")
        return filepath
    
    def write_signal(self, signal_type: str, data: Dict) -> Path:
        """
        Write signal to /Signals/ directory
        
        Signals are lightweight notifications for Local Agent
        """
        signals_dir = self.config.full_signals_path
        signals_dir.mkdir(parents=True, exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{signal_type}_{timestamp}.json"
        filepath = signals_dir / filename
        
        import json
        signal_data = {
            "type": signal_type,
            "timestamp": datetime.now().isoformat(),
            "source": "cloud_agent",
            "data": data,
        }
        
        filepath.write_text(json.dumps(signal_data, indent=2), encoding='utf-8')
        logger.info(f"Wrote signal: {filepath}")
        return filepath


def create_sync_client(config: Optional[CloudConfig] = None) -> CloudSyncClient:
    """Create CloudSyncClient instance"""
    return CloudSyncClient(config)


def start_sync_loop(
    config: Optional[CloudConfig] = None,
    interval: Optional[int] = None,
    max_iterations: Optional[int] = None
):
    """
    Start continuous sync loop
    
    Runs in background thread for continuous sync
    """
    import threading
    import time
    
    client = create_sync_client(config)
    interval = interval or config.sync_interval if config else 60
    
    def sync_loop():
        iteration = 0
        while max_iterations is None or iteration < max_iterations:
            try:
                client.sync()
            except Exception as e:
                logger.error(f"Sync loop error: {e}")
            
            time.sleep(interval)
            iteration += 1
    
    thread = threading.Thread(target=sync_loop, daemon=True)
    thread.start()
    
    logger.info(f"Started sync loop (interval: {interval}s)")
    return thread


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    config = get_config()
    client = create_sync_client(config)
    
    # Initialize git
    if not client.initialize_git():
        logger.error("Failed to initialize Git")
        exit(1)
    
    # Get status
    status = client.get_status()
    logger.info(f"Sync status: {status.status}")
    logger.info(f"Uncommitted: {status.uncommitted_changes}")
    logger.info(f"Unpushed: {status.unpushed_commits}")
    logger.info(f"Unpulled: {status.unpulled_commits}")
