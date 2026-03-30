"""
Local Sync Client

Git-based vault synchronization for Local Agent.
Handles:
- Pulling drafts and action files from Cloud
- Pushing approvals and completions to Cloud
- Merging updates from Cloud into Dashboard.md
- Conflict resolution
"""

import logging
import subprocess
import os
import json
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Optional

from .config import LocalConfig, get_config

logger = logging.getLogger(__name__)


class LocalSyncClient:
    """
    Local Sync Client
    
    Manages Git-based vault sync for Local Agent:
    - Pull changes from Cloud (drafts, action files)
    - Push changes to Cloud (approvals, completions)
    - Merge Cloud updates into Dashboard.md
    - Handle conflicts gracefully
    """
    
    def __init__(self, config: Optional[LocalConfig] = None):
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
            "whatsapp_session/",
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
                with open(gitignore_path, 'a', encoding='utf-8') as f:
                    f.write("\n# Added by Local Sync\n")
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
            self._run_git_command("commit", "-m", "Initial commit - Local Agent setup")
            
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
    
    def pull_changes(self) -> 'SyncStatus':
        """Pull changes from Cloud"""
        from .sync_client import SyncStatus
        status = SyncStatus()
        
        try:
            # Fetch remote changes
            self._run_git_command("fetch", "origin")
            
            # Check for conflicts
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
            
            logger.info(f"Pulled changes from Cloud (sync #{self.sync_count})")
            
        except subprocess.CalledProcessError as e:
            logger.error(f"Git pull failed: {e}")
            status.status = "error"
        except Exception as e:
            logger.error(f"Pull error: {e}")
            status.status = "error"
        
        return status
    
    def push_changes(self) -> 'SyncStatus':
        """Push changes to Cloud"""
        from .sync_client import SyncStatus
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
                "-m", f"Local Agent update - {timestamp}"
            )
            
            # Push changes
            self._run_git_command("push", "origin", self.git_branch)
            
            self.last_push = datetime.now()
            self.sync_count += 1
            
            status.last_push = self.last_push
            status.status = "synced"
            
            logger.info(f"Pushed changes to Cloud (sync #{self.sync_count})")
            
        except subprocess.CalledProcessError as e:
            logger.error(f"Git push failed: {e}")
            status.status = "error"
        except Exception as e:
            logger.error(f"Push error: {e}")
            status.status = "error"
        
        return status
    
    def sync(self) -> 'SyncStatus':
        """Full sync: pull → process → push"""
        logger.info("Starting full sync...")
        
        # Step 1: Pull changes from Cloud
        pull_status = self.pull_changes()
        if pull_status.status == "conflicted":
            logger.error("Cannot sync: conflicts detected")
            return pull_status
        
        # Step 2: Process updates from Cloud
        self._process_cloud_updates()
        
        # Step 3: Push approvals and completions
        push_status = self.push_changes()
        
        return push_status
    
    def _process_cloud_updates(self):
        """
        Process updates from Cloud Agent
        
        - Merge Updates/ into Dashboard.md
        - Process Signals/
        - Track Cloud completions
        """
        self._merge_updates_into_dashboard()
        self._process_signals()
    
    def _merge_updates_into_dashboard(self):
        """Merge Cloud updates into Dashboard.md"""
        updates_dir = self.config.full_updates_path
        
        if not updates_dir.exists():
            return
        
        dashboard_path = self.vault_path / "Dashboard.md"
        
        for update_file in updates_dir.iterdir():
            if not update_file.name.endswith('.md'):
                continue
            
            try:
                update_content = update_file.read_text(encoding='utf-8')
                
                # Parse update
                update_data = self._parse_update(update_content)
                
                # Merge into Dashboard
                self._merge_update_into_dashboard(dashboard_path, update_data)
                
                # Mark update as processed
                processed_dir = updates_dir / "processed"
                processed_dir.mkdir(parents=True, exist_ok=True)
                update_file.rename(processed_dir / update_file.name)
                
                logger.info(f"Merged update: {update_file.name}")
                
            except Exception as e:
                logger.error(f"Error processing update {update_file.name}: {e}")
    
    def _parse_update(self, content: str) -> Dict:
        """Parse update file content"""
        if not content.startswith('---'):
            return {}
        
        end_frontmatter = content.find('---', 3)
        if end_frontmatter == -1:
            return {}
        
        frontmatter = content[4:end_frontmatter].strip()
        metadata = {}
        
        for line in frontmatter.split('\n'):
            if ':' in line:
                key, value = line.split(':', 1)
                metadata[key.strip()] = value.strip()
        
        # Extract body
        body = content[end_frontmatter + 3:].strip()
        
        return {
            "metadata": metadata,
            "content": body,
            "type": metadata.get('type', 'unknown'),
            "timestamp": metadata.get('timestamp', ''),
        }
    
    def _merge_update_into_dashboard(self, dashboard_path: Path, update_data: Dict):
        """Merge update into Dashboard.md"""
        if not dashboard_path.exists():
            # Create new dashboard
            dashboard_path.write_text(
                f"# Dashboard\n\n## Cloud Updates\n\n{update_data['content']}\n",
                encoding='utf-8'
            )
            return
        
        content = dashboard_path.read_text(encoding='utf-8')
        
        # Find or create Cloud Updates section
        if "## Cloud Updates" not in content:
            # Add section
            content += f"\n\n## Cloud Updates\n\n{update_data['content']}\n"
        else:
            # Prepend to existing section
            lines = content.split('\n')
            new_lines = []
            inserted = False
            
            for i, line in enumerate(lines):
                new_lines.append(line)
                if line.startswith("## Cloud Updates") and not inserted:
                    new_lines.append(f"\n{update_data['content']}\n")
                    inserted = True
            
            content = '\n'.join(new_lines)
        
        dashboard_path.write_text(content, encoding='utf-8')
    
    def _process_signals(self):
        """Process signals from Cloud"""
        signals_dir = self.config.full_signals_path
        
        if not signals_dir.exists():
            return
        
        for signal_file in signals_dir.iterdir():
            if not signal_file.name.endswith('.json'):
                continue
            
            try:
                data = json.loads(signal_file.read_text())
                signal_type = data.get('type', 'unknown')
                
                logger.info(f"Processing signal: {signal_type}")
                
                # Move to processed
                processed_dir = signals_dir / "processed"
                processed_dir.mkdir(parents=True, exist_ok=True)
                signal_file.rename(processed_dir / signal_file.name)
                
            except Exception as e:
                logger.error(f"Error processing signal {signal_file.name}: {e}")
    
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
            env={**os.environ, "GIT_TERMINAL_PROMPT": "0"}
        )
        
        if result.returncode != 0:
            raise subprocess.CalledProcessError(
                result.returncode, cmd, result.stdout, result.stderr
            )
        
        return result.stdout
    
    def get_status(self) -> 'SyncStatus':
        """Get current sync status"""
        from .sync_client import SyncStatus
        
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


def create_sync_client(config: Optional[LocalConfig] = None) -> LocalSyncClient:
    """Create LocalSyncClient instance"""
    return LocalSyncClient(config)


# Import SyncStatus for type hints
class SyncStatus:
    last_pull: Optional[datetime] = None
    last_push: Optional[datetime] = None
    uncommitted_changes: int = 0
    unpushed_commits: int = 0
    unpulled_commits: int = 0
    conflicts: List[str] = None
    status: str = "unknown"
    
    def __post_init__(self):
        if self.conflicts is None:
            self.conflicts = []


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
