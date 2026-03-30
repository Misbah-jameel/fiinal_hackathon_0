"""
Local Agent Runner - No Git Required

Run this for pure local deployment without Git sync
"""

import sys
import os
from pathlib import Path

# Add current directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from platinum.local_agent.config import LocalConfig, get_config
from platinum.local_agent.approver import LocalApprover
from platinum.local_agent.executor import LocalExecutor
from platinum.local_agent.notifier import LocalNotifier

import logging
import time

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def main():
    """Run Local Agent in local-only mode (no Git sync)"""
    
    print("=" * 60)
    print("AI Employee - Local Agent")
    print("Mode: LOCAL ONLY (No Git Sync)")
    print("=" * 60)
    
    # Load config
    config = get_config()
    
    print(f"\n✓ Vault Path: {config.vault_path}")
    print(f"✓ Agent ID: {config.agent_id}")
    print(f"✓ DRY_RUN: {config.dry_run}")
    print(f"✓ Desktop Notifications: {config.desktop_notifications}")
    
    # Initialize components
    print("\n📋 Initializing components...")
    approver = LocalApprover(config)
    executor = LocalExecutor(config)
    notifier = LocalNotifier(config)
    
    print("✓ Approver initialized")
    print("✓ Executor initialized")
    print("✓ Notifier initialized")
    
    # Show status
    print("\n" + "=" * 60)
    print("Local Agent Status")
    print("=" * 60)
    
    print(f"\n📊 Pending Approvals: {len(approver.check_pending_approvals())}")
    
    stats = approver.get_statistics()
    print(f"📋 Total Approved: {stats['approved']}")
    print(f"📋 Total Rejected: {stats['rejected']}")
    
    exec_stats = executor.get_statistics()
    print(f"⚙️  Total Executed: {exec_stats['total_executed']}")
    print(f"⚙️  Success Rate: {exec_stats['success_rate']:.1f}%")
    
    # Test notification
    print("\n🔔 Testing notification...")
    notifier.send({
        "title": "Local Agent Started",
        "message": "AI Employee ready for local operation",
        "priority": "low",
    })
    print("✓ Notification sent")
    
    print("\n" + "=" * 60)
    print("✅ Local Agent Ready!")
    print("=" * 60)
    print("\n💡 Next Steps:")
    print("1. Check AI_Employee_Vault/Needs_Action/ for new items")
    print("2. Move files to Pending_Approval/ for processing")
    print("3. Approve actions by moving to Approved/")
    print("4. Local Agent will execute automatically")
    print("\n📁 Vault Location:")
    print(f"   {config.full_vault_path}")
    print("\nPress Ctrl+C to exit")
    
    # Main loop (check approvals every 30 seconds)
    try:
        iteration = 0
        while True:
            # Check for new approvals
            requests = approver.check_pending_approvals()
            
            if requests:
                print(f"\n📋 {len(requests)} approval(s) pending")
                approver.notify_user(requests)
            
            # Process approved files
            count = executor.process_approved_directory()
            if count > 0:
                print(f"⚙️  Executed {count} action(s)")
            
            iteration += 1
            time.sleep(30)
            
    except KeyboardInterrupt:
        print("\n\n👋 Shutting down Local Agent...")
        
        # Final stats
        print("\n📊 Final Statistics:")
        print(f"  Approvals: {approver.get_statistics()}")
        print(f"  Executions: {executor.get_statistics()}")
        print(f"  Notifications: {notifier.get_statistics()}")


if __name__ == "__main__":
    main()
