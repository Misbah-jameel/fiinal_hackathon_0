"""
Local Agent - Main Entry Point

Platinum Tier: Always-On Cloud + Local Executive

This agent runs on your local machine and handles:
- Human approval workflows
- Executing sensitive actions via MCP
- WhatsApp session management
- Banking/payment credentials (never synced)
- Final send/post actions

Security: Secrets NEVER leave this machine
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
from .approver import LocalApprover, create_approver
from .executor import LocalExecutor, create_executor
from .notifier import LocalNotifier, create_notifier
from .sync_client import LocalSyncClient, create_sync_client

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class LocalAgent:
    """
    Local Agent - Desktop Executive
    
    Runs on your local machine, handling approvals and execution.
    Credentials and secrets stay on this machine (never synced to cloud).
    """
    
    def __init__(
        self,
        git_remote: str,
        vault_path: str = "./AI_Employee_Vault",
        agent_id: str = "local_agent",
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
        self.approver = create_approver(self.config)
        self.executor = create_executor(self.config)
        self.notifier = create_notifier(self.config)
        self.sync_client = create_sync_client(self.config)
        
        # State
        self.running = False
        self.start_time: Optional[datetime] = None
        
        # Setup signal handlers
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
        
        # Register callbacks
        self.approver.register_approval_callback(self._on_approval)
        self.approver.register_rejection_callback(self._on_rejection)
    
    def _signal_handler(self, signum, frame):
        """Handle shutdown signals"""
        logger.info(f"Received signal {signum}, shutting down...")
        self.stop()
        sys.exit(0)
    
    def _on_approval(self, request):
        """Callback when approval is granted"""
        logger.info(f"Approval granted: {request.action_type}")
        self.notifier.notify_execution_complete(request.action_type, True)
    
    def _on_rejection(self, request):
        """Callback when approval is rejected"""
        logger.info(f"Approval rejected: {request.action_type}")
    
    def initialize(self) -> bool:
        """
        Initialize Local Agent
        
        - Setup Git repository (if not exists)
        - Create required directories
        - Initial sync from cloud
        """
        logger.info("Initializing Local Agent...")
        
        # Ensure directories exist
        self.config.ensure_directories()
        
        # Initialize Git (if needed)
        if not self.sync_client.initialize_git():
            logger.error("Failed to initialize Git")
            return False
        
        # Configure remote if provided
        if self.git_remote:
            if not self.sync_client.configure_remote(self.git_remote):
                logger.error("Failed to configure Git remote")
                return False
        
        # Initial sync from cloud
        logger.info("Performing initial sync from cloud...")
        status = self.sync_client.sync()
        if status.status != "synced":
            logger.warning(f"Initial sync status: {status.status}")
        
        logger.info("Local Agent initialized successfully")
        return True
    
    def start(self):
        """Start Local Agent"""
        if self.running:
            logger.warning("Local Agent already running")
            return
        
        logger.info("Starting Local Agent...")
        self.running = True
        self.start_time = datetime.now()
        
        # Notify startup
        self.notifier.send({
            "title": "🤖 Local Agent Started",
            "message": f"AI Employee ready at {datetime.now().strftime('%H:%M')}",
            "priority": "low",
        })
        
        # Main loop
        self._run_main_loop()
    
    def _run_main_loop(self):
        """Run main agent loop"""
        logger.info("Starting main agent loop...")
        
        sync_interval = self.config.sync_interval
        approval_check_interval = 30  # Check approvals every 30 seconds
        
        last_sync = 0
        last_approval_check = 0
        
        while self.running:
            try:
                current_time = time.time()
                
                # Sync with cloud
                if current_time - last_sync >= sync_interval:
                    self._sync_with_cloud()
                    last_sync = current_time
                
                # Check approvals
                if current_time - last_approval_check >= approval_check_interval:
                    self._check_and_process_approvals()
                    last_approval_check = current_time
                
                # Process approved files
                self._process_approved_files()
                
                # Check for signals from cloud
                self._process_cloud_signals()
                
                # Wait
                time.sleep(5)
                
            except Exception as e:
                logger.error(f"Main loop error: {e}")
                time.sleep(5)
    
    def _sync_with_cloud(self):
        """Sync with cloud agent"""
        try:
            status = self.sync_client.sync()
            
            if status.status == "synced":
                logger.debug("Sync completed successfully")
            elif status.status == "conflicted":
                logger.warning("Sync conflicts detected")
                self.notifier.notify_error("Vault sync conflicts detected")
            
            # Notify on significant changes
            changes = (
                status.uncommitted_changes +
                status.unpushed_commits +
                status.unpulled_commits
            )
            if changes > 0:
                self.notifier.notify_sync_complete(status.status, changes)
                
        except Exception as e:
            logger.error(f"Sync failed: {e}")
    
    def _check_and_process_approvals(self):
        """Check for new approvals and notify user"""
        try:
            requests = self.approver.check_pending_approvals()
            
            if requests:
                # Group by action type
                action_types = list(set(r.action_type for r in requests))
                self.approver.notify_user(requests)
                self.notifier.notify_approval_pending(len(requests), action_types)
                
                # Log pending count
                logger.info(f"📋 {len(requests)} approval(s) pending")
                
        except Exception as e:
            logger.error(f"Approval check failed: {e}")
    
    def _process_approved_files(self):
        """Process files in /Approved/ directory"""
        try:
            count = self.executor.process_approved_directory()
            if count > 0:
                logger.info(f"Executed {count} approved action(s)")
        except Exception as e:
            logger.error(f"Execution failed: {e}")
    
    def _process_cloud_signals(self):
        """Process signals from cloud agent"""
        signals_dir = self.config.full_signals_path
        
        if not signals_dir.exists():
            return
        
        for signal_file in signals_dir.iterdir():
            if not signal_file.name.endswith('.json'):
                continue
            
            try:
                import json
                data = json.loads(signal_file.read_text())
                
                signal_type = data.get('type', 'unknown')
                signal_data = data.get('data', {})
                
                logger.info(f"Processing cloud signal: {signal_type}")
                
                # Handle different signal types
                if signal_type == "draft_ready":
                    self.notifier.send({
                        "title": "📝 Draft Ready",
                        "message": f"New draft from Cloud Agent: {signal_data.get('draft_type', 'unknown')}",
                        "priority": "low",
                    })
                elif signal_type == "lead_detected":
                    self.notifier.notify_lead_detected(
                        signal_data.get('priority', 'P3'),
                        signal_data.get('source', 'unknown'),
                    )
                elif signal_type == "urgent":
                    self.notifier.notify_error(
                        f"Urgent from Cloud: {signal_data.get('message', '')}"
                    )
                
                # Move processed signal to done
                done_dir = signals_dir / "processed"
                done_dir.mkdir(parents=True, exist_ok=True)
                signal_file.rename(done_dir / signal_file.name)
                
            except Exception as e:
                logger.error(f"Error processing signal {signal_file.name}: {e}")
    
    def stop(self):
        """Stop Local Agent"""
        logger.info("Stopping Local Agent...")
        self.running = False
        
        # Final sync
        try:
            self.sync_client.sync()
            logger.info("Final sync completed")
        except Exception as e:
            logger.error(f"Final sync failed: {e}")
        
        # Notify shutdown
        self.notifier.send({
            "title": "😴 Local Agent Stopped",
            "message": f"Ran for {datetime.now() - self.start_time}",
            "priority": "low",
        })
        
        # Log runtime
        if self.start_time:
            runtime = datetime.now() - self.start_time
            logger.info(f"Local Agent ran for {runtime}")
    
    def status(self) -> dict:
        """Get Local Agent status"""
        sync_status = self.sync_client.get_status()
        
        return {
            "agent_id": self.agent_id,
            "running": self.running,
            "start_time": self.start_time.isoformat() if self.start_time else None,
            "uptime": str(datetime.now() - self.start_time) if self.start_time else None,
            "sync_status": sync_status.status,
            "last_pull": sync_status.last_pull.isoformat() if sync_status.last_pull else None,
            "last_push": sync_status.last_push.isoformat() if sync_status.last_push else None,
            "approval_stats": self.approver.get_statistics(),
            "execution_stats": self.executor.get_statistics(),
            "notification_stats": self.notifier.get_statistics(),
        }
    
    def run_demo(self, iterations: int = 5):
        """Run demo mode for testing"""
        logger.info(f"Running demo mode ({iterations} iterations)...")
        
        for i in range(iterations):
            logger.info(f"Demo iteration {i + 1}/{iterations}")
            
            # Simulate approval file
            self._simulate_approval_file()
            
            # Check approvals
            self._check_and_process_approvals()
            
            # Show stats
            stats = self.status()
            logger.info(f"Pending approvals: {stats['approval_stats']['pending']}")
            
            time.sleep(2)
        
        logger.info("Demo completed")
    
    def _simulate_approval_file(self):
        """Create simulated approval file for testing"""
        from datetime import timedelta
        
        approval_dir = self.config.full_pending_approval_path
        approval_dir.mkdir(parents=True, exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"APPROVAL_demo_{timestamp}.md"
        filepath = approval_dir / filename
        
        content = f"""---
type: approval_request
action: email_send
created: {datetime.now().isoformat()}
expires: {(datetime.now() + timedelta(hours=24)).isoformat()}
status: pending
cloud_generated: false
---

# Demo Approval Request

**Action:** Email Send
**Created:** {datetime.now().strftime('%Y-%m-%d %H:%M')}

## Content

This is a demo approval request for testing.

## To Approve

Move this file to `/Approved/` to execute.
"""
        
        filepath.write_text(content, encoding='utf-8')
        logger.info(f"Created demo approval file: {filepath}")


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description="Local Agent - Platinum Tier")
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
        default="local_agent",
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
    agent = LocalAgent(
        git_remote=args.git_remote,
        vault_path=args.vault_path,
        agent_id=args.agent_id,
    )
    
    # Initialize
    if not agent.initialize():
        logger.error("Failed to initialize Local Agent")
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
