"""
Cloud Agent - Main Entry Point

Platinum Tier: Always-On Cloud Executive

This agent runs 24/7 on a cloud VM and handles:
- Email triage and draft replies
- Social media monitoring and draft posts
- Lead capture and prioritization
- Draft-only actions (requires Local approval)

Architecture:
1. Watchers monitor external channels
2. Drafter generates responses using Claude Code
3. Sync Client syncs with Local Agent via Git
4. All sensitive actions require Local approval
"""

import logging
import argparse
import signal
import sys
import time
from pathlib import Path
from datetime import datetime
from typing import Optional

from .config import get_config, init_config
from .watcher import create_all_cloud_watchers, start_all_watchers
from .drafter import CloudDrafter
from .sync_client import CloudSyncClient, start_sync_loop

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class CloudAgent:
    """
    Cloud Agent - Always-On Executive
    
    Runs on cloud VM 24/7, handling perception and drafting.
    Execution requires Local Agent approval.
    """
    
    def __init__(
        self,
        git_remote: str,
        vault_path: str = "./AI_Employee_Vault",
        agent_id: str = "cloud_agent",
    ):
        self.git_remote = git_remote
        self.vault_path = Path(vault_path).resolve()
        self.agent_id = agent_id
        
        # Initialize config
        self.config = init_config(
            git_remote=git_remote,
            vault_path=vault_path,
            agent_id=agent_id,
        )
        
        # Initialize components
        self.watchers = []
        self.drafter = CloudDrafter(self.config)
        self.sync_client = CloudSyncClient(self.config)
        
        # State
        self.running = False
        self.start_time: Optional[datetime] = None
        
        # Setup signal handlers
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
    
    def _signal_handler(self, signum, frame):
        """Handle shutdown signals"""
        logger.info(f"Received signal {signum}, shutting down...")
        self.stop()
        sys.exit(0)
    
    def initialize(self) -> bool:
        """
        Initialize Cloud Agent
        
        - Setup Git repository
        - Create required directories
        - Initialize watchers
        """
        logger.info("Initializing Cloud Agent...")
        
        # Ensure directories exist
        self.config.ensure_directories()
        
        # Initialize Git
        if not self.sync_client.initialize_git():
            logger.error("Failed to initialize Git")
            return False
        
        # Configure remote if provided
        if self.git_remote:
            if not self.sync_client.configure_remote(self.git_remote):
                logger.error("Failed to configure Git remote")
                return False
        
        # Create watchers
        self.watchers = create_all_cloud_watchers(self.config)
        logger.info(f"Created {len(self.watchers)} watchers")
        
        # Initial sync
        logger.info("Performing initial sync...")
        status = self.sync_client.sync()
        if status.status != "synced":
            logger.warning(f"Initial sync status: {status.status}")
        
        logger.info("Cloud Agent initialized successfully")
        return True
    
    def start(self):
        """Start Cloud Agent"""
        if self.running:
            logger.warning("Cloud Agent already running")
            return
        
        logger.info("Starting Cloud Agent...")
        self.running = True
        self.start_time = datetime.now()
        
        # Start watchers in background threads
        watcher_threads = start_all_watchers(self.config)
        logger.info(f"Started {len(watcher_threads)} watcher threads")
        
        # Start sync loop in background thread
        sync_thread = start_sync_loop(self.config)
        logger.info("Started sync loop")
        
        # Main drafter loop (process action files periodically)
        self._run_drafter_loop()
    
    def _run_drafter_loop(self, interval: int = 60):
        """Run drafter processing loop"""
        logger.info("Starting drafter loop...")
        
        while self.running:
            try:
                # Process action files and generate drafts
                count = self.drafter.process_all_action_files()
                if count > 0:
                    logger.info(f"Generated {count} new drafts")
                
                # Create approval files for ready drafts
                for draft in self.drafter.get_pending_drafts():
                    self.sync_client.create_approval_file(draft)
                    draft.status = "submitted"
                
                # Cleanup expired drafts
                expired = self.drafter.cleanup_expired_drafts()
                if expired > 0:
                    logger.info(f"Cleaned up {expired} expired drafts")
                
                # Sync with remote
                self.sync_client.sync()
                
            except Exception as e:
                logger.error(f"Drafter loop error: {e}")
            
            time.sleep(interval)
    
    def stop(self):
        """Stop Cloud Agent"""
        logger.info("Stopping Cloud Agent...")
        self.running = False
        
        # Final sync
        try:
            self.sync_client.sync()
            logger.info("Final sync completed")
        except Exception as e:
            logger.error(f"Final sync failed: {e}")
        
        # Log runtime
        if self.start_time:
            runtime = datetime.now() - self.start_time
            logger.info(f"Cloud Agent ran for {runtime}")
    
    def status(self) -> dict:
        """Get Cloud Agent status"""
        sync_status = self.sync_client.get_status()
        
        return {
            "agent_id": self.agent_id,
            "running": self.running,
            "start_time": self.start_time.isoformat() if self.start_time else None,
            "uptime": str(datetime.now() - self.start_time) if self.start_time else None,
            "sync_status": sync_status.status,
            "last_pull": sync_status.last_pull.isoformat() if sync_status.last_pull else None,
            "last_push": sync_status.last_push.isoformat() if sync_status.last_push else None,
            "draft_stats": self.drafter.get_draft_count(),
            "watchers": [w.get_status() for w in self.watchers],
        }
    
    def run_demo(self, iterations: int = 5):
        """
        Run demo mode for testing
        
        Processes action files without actual API calls
        """
        logger.info(f"Running demo mode ({iterations} iterations)...")
        
        for i in range(iterations):
            logger.info(f"Demo iteration {i + 1}/{iterations}")
            
            # Simulate watcher creating action file
            self._simulate_action_file()
            
            # Process action files
            count = self.drafter.process_all_action_files()
            logger.info(f"Generated {count} drafts")
            
            # Show draft stats
            stats = self.drafter.get_draft_count()
            logger.info(f"Draft stats: {stats}")
            
            time.sleep(2)
        
        logger.info("Demo completed")
    
    def _simulate_action_file(self):
        """Create a simulated action file for testing"""
        from .watcher import WatcherItem
        
        # Create test action file
        test_item = WatcherItem(
            id=f"test_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            type="email",
            source="gmail",
            content="Test email for demo",
            metadata={"from": "test@example.com", "subject": "Demo Test"},
        )
        
        # Create action file
        watcher = self.watchers[0] if self.watchers else None
        if watcher:
            filepath = watcher.create_action_file(test_item)
            logger.info(f"Created test action file: {filepath}")


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description="Cloud Agent - Platinum Tier")
    parser.add_argument(
        "--git-remote",
        required=True,
        help="Git remote URL for vault sync"
    )
    parser.add_argument(
        "--vault-path",
        default="./AI_Employee_Vault",
        help="Path to Obsidian vault"
    )
    parser.add_argument(
        "--agent-id",
        default="cloud_agent",
        help="Agent identifier"
    )
    parser.add_argument(
        "--demo",
        action="store_true",
        help="Run in demo mode"
    )
    parser.add_argument(
        "--status",
        action="store_true",
        help="Show agent status and exit"
    )
    parser.add_argument(
        "--init-only",
        action="store_true",
        help="Initialize and exit"
    )
    
    args = parser.parse_args()
    
    # Create agent
    agent = CloudAgent(
        git_remote=args.git_remote,
        vault_path=args.vault_path,
        agent_id=args.agent_id,
    )
    
    # Initialize
    if not agent.initialize():
        logger.error("Failed to initialize Cloud Agent")
        sys.exit(1)
    
    # Show status
    if args.status:
        status = agent.status()
        import json
        print(json.dumps(status, indent=2))
        sys.exit(0)
    
    # Init only
    if args.init_only:
        logger.info("Initialization complete")
        sys.exit(0)
    
    # Demo mode
    if args.demo:
        agent.run_demo()
        sys.exit(0)
    
    # Start agent
    agent.start()


if __name__ == "__main__":
    main()
