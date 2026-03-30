"""
Platinum Tier Demo Flow

End-to-end demonstration of Platinum Tier features:
1. Cloud Agent receives email
2. Cloud Agent creates draft reply
3. Cloud Agent writes approval file
4. Git sync pushes to Local
5. Local Agent notifies user
6. User approves (moves file)
7. Local Agent executes via MCP
8. Local Agent moves to Done
9. Git sync pushes completion to Cloud

This demo simulates the full Platinum workflow without actual API calls.
"""

import logging
import time
import shutil
from pathlib import Path
from datetime import datetime, timedelta
from typing import Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class PlatinumDemo:
    """
    Platinum Tier Demo Flow
    
    Demonstrates the complete Cloud → Local workflow
    """
    
    def __init__(self, vault_path: str = "./AI_Employee_Vault"):
        self.vault_path = Path(vault_path).resolve()
        self.demo_dir = self.vault_path / "Platinum_Demo"
        
        # Directories
        self.needs_action = self.vault_path / "Needs_Action"
        self.plans = self.vault_path / "Plans"
        self.pending_approval = self.vault_path / "Pending_Approval"
        self.approved = self.vault_path / "Approved"
        self.done = self.vault_path / "Done"
        self.in_progress = self.vault_path / "In_Progress"
        self.updates = self.vault_path / "Updates"
        self.signals = self.vault_path / "Signals"
        
        # Ensure directories exist
        self._ensure_directories()
        
        # Demo state
        self.step = 0
        self.start_time: Optional[datetime] = None
    
    def _ensure_directories(self):
        """Create all required directories"""
        dirs = [
            self.vault_path,
            self.demo_dir,
            self.needs_action / "gmail",
            self.plans / "drafts",
            self.pending_approval,
            self.approved,
            self.done,
            self.in_progress / "cloud_agent",
            self.in_progress / "local_agent",
            self.updates,
            self.signals,
        ]
        for d in dirs:
            d.mkdir(parents=True, exist_ok=True)
    
    def run_demo(self, speed: float = 1.0):
        """
        Run complete demo flow
        
        Args:
            speed: Multiplier for wait times (1.0 = normal, 0.5 = fast)
        """
        self.start_time = datetime.now()
        
        logger.info("=" * 60)
        logger.info("PLATINUM TIER DEMO - End-to-End Workflow")
        logger.info("=" * 60)
        logger.info(f"Vault: {self.vault_path}")
        logger.info(f"Start time: {self.start_time.strftime('%Y-%m-%d %H:%M:%S')}")
        logger.info("")
        
        # Step 1: Email arrives (Cloud detects)
        self._step_1_email_arrives(speed)
        
        # Step 2: Cloud creates draft reply
        self._step_2_cloud_creates_draft(speed)
        
        # Step 3: Cloud creates approval file
        self._step_3_cloud_creates_approval(speed)
        
        # Step 4: Cloud syncs to Local (Git push)
        self._step_4_cloud_syncs(speed)
        
        # Step 5: Local notifies user
        self._step_5_local_notifies(speed)
        
        # Step 6: User approves (simulated)
        self._step_6_user_approves(speed)
        
        # Step 7: Local executes via MCP
        self._step_7_local_executes(speed)
        
        # Step 8: Local moves to Done
        self._step_8_moves_to_done(speed)
        
        # Step 9: Local syncs completion to Cloud
        self._step_9_local_syncs(speed)
        
        # Demo complete
        self._demo_complete()
    
    def _wait(self, seconds: float):
        """Wait with logging"""
        time.sleep(seconds)
    
    def _step_1_email_arrives(self, speed: float):
        """Step 1: Email arrives, Cloud detects"""
        self.step = 1
        logger.info("-" * 60)
        logger.info("STEP 1: Email Arrives (Cloud Detection)")
        logger.info("-" * 60)
        
        # Create simulated email action file
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        email_content = f"""---
type: email
source: gmail
item_id: demo_email_{timestamp}
from: client@example.com
subject: Pricing Inquiry
received: {datetime.now().isoformat()}
priority: P2
status: pending
cloud_processed: {datetime.now().isoformat()}
---

# Email — Action Required

**Source:** gmail
**From:** client@example.com
**Subject:** Pricing Inquiry
**Received:** {datetime.now().strftime('%Y-%m-%d %H:%M')}

## Content

Hi,

I'm interested in your services. Could you please send me pricing information?

Thanks,
Client

## Suggested Actions

- [ ] Generate pricing response
- [ ] Send via email (requires approval)
- [ ] Log interaction

---
*Created by Cloud Agent (Gmail Watcher)*
"""
        
        email_file = self.needs_action / "gmail" / f"EMAIL_demo_{timestamp}.md"
        email_file.write_text(email_content, encoding='utf-8')
        
        logger.info(f"✅ Email action file created: {email_file.name}")
        logger.info(f"   Location: {self.needs_action / 'gmail'}/")
        
        self._wait(2.0 * speed)
    
    def _step_2_cloud_creates_draft(self, speed: float):
        """Step 2: Cloud Agent creates draft reply"""
        self.step = 2
        logger.info("")
        logger.info("-" * 60)
        logger.info("STEP 2: Cloud Agent Creates Draft Reply")
        logger.info("-" * 60)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        draft_content = f"""---
type: email_draft
in_reply_to: demo_email_{timestamp}
draft_generated: {datetime.now().isoformat()}
status: pending_review
---

# Draft Email Reply

**To:** client@example.com
**Subject:** Re: Pricing Inquiry

---

Dear Valued Client,

Thank you for your interest in our services!

## Pricing Information

Our standard pricing tiers are:

1. **Basic Plan**: $500/month
   - Email support
   - Monthly reports
   - 5 projects

2. **Professional Plan**: $1,000/month
   - Priority support
   - Weekly reports
   - 15 projects
   - API access

3. **Enterprise Plan**: $2,500/month
   - 24/7 support
   - Daily reports
   - Unlimited projects
   - Full API access
   - Dedicated account manager

## Next Steps

I'd be happy to schedule a call to discuss your specific needs.
Are you available for a 30-minute consultation this week?

Best regards,
AI Employee
Your Company

---
*Draft generated by Cloud Agent — requires Local Agent approval before sending*
"""
        
        draft_file = self.plans / "drafts" / f"DRAFT_email_demo_{timestamp}.md"
        draft_file.write_text(draft_content, encoding='utf-8')
        
        logger.info(f"✅ Draft reply created: {draft_file.name}")
        logger.info(f"   Location: {self.plans / 'drafts'}/")
        
        self._wait(2.0 * speed)
    
    def _step_3_cloud_creates_approval(self, speed: float):
        """Step 3: Cloud creates approval file"""
        self.step = 3
        logger.info("")
        logger.info("-" * 60)
        logger.info("STEP 3: Cloud Creates Approval File")
        logger.info("-" * 60)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        approval_content = f"""---
type: approval_request
action: email_send
draft_id: email_demo_{timestamp}
created: {datetime.now().isoformat()}
expires: {(datetime.now() + timedelta(hours=24)).isoformat()}
status: pending
cloud_generated: true
to: client@example.com
subject: Re: Pricing Inquiry
---

# Action Required: Email Send

**Draft ID:** email_demo_{timestamp}
**Created:** {datetime.now().strftime('%Y-%m-%d %H:%M')}
**Expires:** {(datetime.now() + timedelta(hours=24)).strftime('%Y-%m-%d %H:%M')}
**Generated by:** Cloud Agent

## Draft Content

See: ../Plans/drafts/DRAFT_email_demo_{timestamp}.md

**To:** client@example.com
**Subject:** Re: Pricing Inquiry

## To Approve

1. Review the draft content
2. Move this file to `/Approved/` to execute
3. OR move to `/Rejected/` to cancel

## To Modify

1. Copy this file
2. Edit the draft content
3. Move modified version to `/Approved/`

---
*Cloud Agent: Draft ready for Local Agent approval*
*Execution requires Local Agent (has credentials and MCP access)*
"""
        
        approval_file = self.pending_approval / f"APPROVAL_email_demo_{timestamp}.md"
        approval_file.write_text(approval_content, encoding='utf-8')
        
        logger.info(f"✅ Approval file created: {approval_file.name}")
        logger.info(f"   Location: {self.pending_approval}/")
        logger.info(f"   Awaiting: User/Local Agent approval")
        
        self._wait(2.0 * speed)
    
    def _step_4_cloud_syncs(self, speed: float):
        """Step 4: Cloud syncs to Local (Git push)"""
        self.step = 4
        logger.info("")
        logger.info("-" * 60)
        logger.info("STEP 4: Cloud Syncs to Local (Git Push)")
        logger.info("-" * 60)
        
        # Simulate Git sync
        sync_signal = self.signals / f"sync_complete_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        sync_content = f"""{{
  "type": "sync_complete",
  "timestamp": "{datetime.now().isoformat()}",
  "source": "cloud_agent",
  "data": {{
    "status": "success",
    "files_pushed": 3,
    "approval_pending": true
  }}
}}
"""
        sync_signal.write_text(sync_content, encoding='utf-8')
        
        logger.info("✅ Cloud Agent pushed changes via Git")
        logger.info(f"   Files pushed: 3 (action file, draft, approval)")
        logger.info(f"   Sync signal: {sync_signal.name}")
        
        self._wait(2.0 * speed)
    
    def _step_5_local_notifies(self, speed: float):
        """Step 5: Local Agent notifies user"""
        self.step = 5
        logger.info("")
        logger.info("-" * 60)
        logger.info("STEP 5: Local Agent Notifies User")
        logger.info("-" * 60)
        
        logger.info("📬 Local Agent detected pending approval")
        logger.info("🔔 Desktop notification sent")
        logger.info("🔊 Notification sound played")
        logger.info("")
        logger.info("   Notification content:")
        logger.info("   ┌────────────────────────────────────────────────────┐")
        logger.info("   │ 📋 Approval Required                              │")
        logger.info("   │ 1 action awaiting your approval                   │")
        logger.info("   │ Action: email_send                                │")
        logger.info("   └────────────────────────────────────────────────────┘")
        
        self._wait(3.0 * speed)
    
    def _step_6_user_approves(self, speed: float):
        """Step 6: User approves (simulated)"""
        self.step = 6
        logger.info("")
        logger.info("-" * 60)
        logger.info("STEP 6: User Approves (Simulated)")
        logger.info("-" * 60)
        
        # Find approval file
        approval_files = list(self.pending_approval.glob("APPROVAL_*.md"))
        if not approval_files:
            logger.error("❌ No approval file found!")
            return
        
        approval_file = approval_files[0]
        
        logger.info(f"📋 User reviews: {approval_file.name}")
        logger.info("✅ User moves file to /Approved/")
        
        # Simulate user moving file
        approved_file = self.approved / approval_file.name
        shutil.move(str(approval_file), str(approved_file))
        
        logger.info(f"   From: {self.pending_approval}/")
        logger.info(f"   To:   {self.approved}/")
        
        self._wait(2.0 * speed)
    
    def _step_7_local_executes(self, speed: float):
        """Step 7: Local Agent executes via MCP"""
        self.step = 7
        logger.info("")
        logger.info("-" * 60)
        logger.info("STEP 7: Local Agent Executes via MCP")
        logger.info("-" * 60)
        
        logger.info("🔄 Local Agent processing approved file...")
        logger.info("📧 Calling Email MCP to send...")
        logger.info("")
        
        # Simulate execution
        execution_log = self.demo_dir / f"execution_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
        execution_content = f"""# Execution Log

**Time:** {datetime.now().isoformat()}
**Action:** email_send
**Actor:** local_agent
**Status:** success

## MCP Call

```
email_send(
    to="client@example.com",
    subject="Re: Pricing Inquiry",
    body="..."
)
```

## Result

```json
{{
  "success": true,
  "message_id": "<demo_message_id@example.com>",
  "timestamp": "{datetime.now().isoformat()}"
}}
```

## Audit Entry

- Action logged to: /Audit/json/{datetime.now().strftime('%Y-%m-%d')}.jsonl
- Email send recorded
- Interaction logged
"""
        execution_log.write_text(execution_content, encoding='utf-8')
        
        logger.info(f"✅ Email sent successfully")
        logger.info(f"   Message ID: <demo_message_id@example.com>")
        logger.info(f"   Execution log: {execution_log.name}")
        
        self._wait(2.0 * speed)
    
    def _step_8_moves_to_done(self, speed: float):
        """Step 8: Local moves to Done"""
        self.step = 8
        logger.info("")
        logger.info("-" * 60)
        logger.info("STEP 8: Local Moves to Done")
        logger.info("-" * 60)
        
        # Find approved file
        approved_files = list(self.approved.glob("APPROVAL_*.md"))
        if not approved_files:
            logger.error("❌ No approved file found!")
            return
        
        approved_file = approved_files[0]
        
        logger.info(f"📁 Moving completed action to /Done/")
        
        # Simulate moving to Done
        done_file = self.done / approved_file.name
        shutil.move(str(approved_file), str(done_file))
        
        logger.info(f"   From: {self.approved}/")
        logger.info(f"   To:   {self.done}/")
        logger.info(f"   Status: Complete ✅")
        
        self._wait(2.0 * speed)
    
    def _step_9_local_syncs(self, speed: float):
        """Step 9: Local syncs completion to Cloud"""
        self.step = 9
        logger.info("")
        logger.info("-" * 60)
        logger.info("STEP 9: Local Syncs Completion to Cloud")
        logger.info("-" * 60)
        
        # Simulate Git sync
        completion_signal = self.signals / f"completion_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        completion_content = f"""{{
  "type": "action_complete",
  "timestamp": "{datetime.now().isoformat()}",
  "source": "local_agent",
  "data": {{
    "action_type": "email_send",
    "status": "success",
    "message_id": "<demo_message_id@example.com>"
  }}
}}
"""
        completion_signal.write_text(completion_content, encoding='utf-8')
        
        logger.info("✅ Local Agent pushed completion via Git")
        logger.info(f"   Completion signal: {completion_signal.name}")
        logger.info(f"   Cloud Agent will detect on next sync")
        
        self._wait(2.0 * speed)
    
    def _demo_complete(self):
        """Demo complete summary"""
        logger.info("")
        logger.info("=" * 60)
        logger.info("DEMO COMPLETE! ✅")
        logger.info("=" * 60)
        
        end_time = datetime.now()
        runtime = end_time - self.start_time
        
        logger.info("")
        logger.info("📊 Demo Summary:")
        logger.info(f"   Total steps: {self.step}")
        logger.info(f"   Runtime: {runtime.total_seconds():.1f} seconds")
        logger.info(f"   Start: {self.start_time.strftime('%Y-%m-%d %H:%M:%S')}")
        logger.info(f"   End: {end_time.strftime('%Y-%m-%d %H:%M:%S')}")
        logger.info("")
        logger.info("📁 Files Created:")
        logger.info(f"   - Action file: /Needs_Action/gmail/EMAIL_demo_*.md")
        logger.info(f"   - Draft: /Plans/drafts/DRAFT_email_demo_*.md")
        logger.info(f"   - Approval: /Pending_Approval/APPROVAL_email_demo_*.md → /Approved/ → /Done/")
        logger.info(f"   - Execution log: /Platinum_Demo/execution_*.log")
        logger.info(f"   - Sync signals: /Signals/sync_*.json, completion_*.json")
        logger.info("")
        logger.info("🎯 Platinum Tier Features Demonstrated:")
        logger.info("   ✅ Cloud Agent: Email detection & draft creation")
        logger.info("   ✅ Work-Zone Specialization: Cloud drafts, Local executes")
        logger.info("   ✅ Vault Sync: Git-based file synchronization")
        logger.info("   ✅ Human-in-the-Loop: Approval workflow")
        logger.info("   ✅ Local Agent: MCP execution with credentials")
        logger.info("   ✅ Audit Trail: Complete execution logging")
        logger.info("")
        logger.info("🚀 Next Steps:")
        logger.info("   1. Configure Git remote for real sync")
        logger.info("   2. Deploy Cloud Agent to VM")
        logger.info("   3. Configure credentials in Local Agent")
        logger.info("   4. Run with actual API integrations")
        logger.info("")


def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Platinum Tier Demo Flow")
    parser.add_argument(
        "--vault",
        default="./AI_Employee_Vault",
        help="Path to Obsidian vault"
    )
    parser.add_argument(
        "--speed",
        type=float,
        default=1.0,
        help="Demo speed multiplier (1.0 = normal, 0.5 = fast, 2.0 = slow)"
    )
    
    args = parser.parse_args()
    
    demo = PlatinumDemo(vault_path=args.vault)
    demo.run_demo(speed=args.speed)


if __name__ == "__main__":
    main()
