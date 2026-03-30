"""
Cloud Drafter

Generates draft responses for:
- Email replies
- Social media posts
- Invoice creation
- Lead responses

All drafts are stored in /Plans/ or /Pending_Approval/ for Local Agent review.
Cloud Agent NEVER executes send/post/pay actions directly.
"""

import logging
from pathlib import Path
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Any
from dataclasses import dataclass, field
import json
import subprocess

from .config import CloudConfig, get_config

logger = logging.getLogger(__name__)


@dataclass
class Draft:
    """Represents a draft action"""
    id: str
    type: str  # email, social_post, invoice, response
    content: str
    metadata: Dict[str, Any] = field(default_factory=dict)
    created: datetime = field(default_factory=datetime.now)
    expires: datetime = field(default_factory=lambda: datetime.now() + timedelta(hours=24))
    status: str = "pending"  # pending, approved, rejected, expired
    source_file: Optional[Path] = None


class CloudDrafter:
    """
    Cloud Drafter
    
    Uses Claude Code to generate draft responses and actions.
    All drafts require Local Agent approval before execution.
    """
    
    def __init__(self, config: Optional[CloudConfig] = None):
        self.config = config or get_config()
        self.drafts: List[Draft] = []
        self.max_pending = self.config.max_drafts_pending
    
    def generate_email_draft(self, action_file: Path) -> Optional[Draft]:
        """
        Generate draft email reply using Claude Code
        
        Reads action file, applies Company Handbook rules,
        and creates draft response
        """
        try:
            content = action_file.read_text(encoding='utf-8')
            
            # Use Claude Code to generate draft
            draft_content = self._invoke_claude_for_draft(
                action_file=action_file,
                draft_type="email"
            )
            
            if not draft_content:
                return None
            
            draft = Draft(
                id=f"email_{action_file.stem}",
                type="email",
                content=draft_content,
                metadata={
                    "source_file": str(action_file),
                    "action_type": "email_reply",
                },
                source_file=action_file,
            )
            
            self.drafts.append(draft)
            self._save_draft(draft)
            
            logger.info(f"Generated email draft: {draft.id}")
            return draft
            
        except Exception as e:
            logger.error(f"Error generating email draft: {e}")
            return None
    
    def generate_social_draft(self, action_file: Path, platform: str) -> Optional[Draft]:
        """Generate draft social media post/reply"""
        try:
            draft_content = self._invoke_claude_for_draft(
                action_file=action_file,
                draft_type="social",
                platform=platform,
            )
            
            if not draft_content:
                return None
            
            draft = Draft(
                id=f"social_{platform}_{action_file.stem}",
                type="social",
                content=draft_content,
                metadata={
                    "source_file": str(action_file),
                    "platform": platform,
                    "action_type": "social_post",
                },
                source_file=action_file,
            )
            
            self.drafts.append(draft)
            self._save_draft(draft)
            
            logger.info(f"Generated {platform} draft: {draft.id}")
            return draft
            
        except Exception as e:
            logger.error(f"Error generating social draft: {e}")
            return None
    
    def generate_invoice_draft(self, action_file: Path) -> Optional[Draft]:
        """Generate draft invoice for Odoo"""
        try:
            draft_content = self._invoke_claude_for_draft(
                action_file=action_file,
                draft_type="invoice",
            )
            
            if not draft_content:
                return None
            
            draft = Draft(
                id=f"invoice_{action_file.stem}",
                type="invoice",
                content=draft_content,
                metadata={
                    "source_file": str(action_file),
                    "action_type": "invoice_create",
                },
                source_file=action_file,
            )
            
            self.drafts.append(draft)
            self._save_draft(draft)
            
            logger.info(f"Generated invoice draft: {draft.id}")
            return draft
            
        except Exception as e:
            logger.error(f"Error generating invoice draft: {e}")
            return None
    
    def generate_lead_response(self, action_file: Path) -> Optional[Draft]:
        """Generate prioritized lead response"""
        try:
            draft_content = self._invoke_claude_for_draft(
                action_file=action_file,
                draft_type="lead_response",
            )
            
            if not draft_content:
                return None
            
            draft = Draft(
                id=f"lead_{action_file.stem}",
                type="lead_response",
                content=draft_content,
                metadata={
                    "source_file": str(action_file),
                    "action_type": "lead_followup",
                    "priority": "high",
                },
                source_file=action_file,
            )
            
            self.drafts.append(draft)
            self._save_draft(draft)
            
            logger.info(f"Generated lead response draft: {draft.id}")
            return draft
            
        except Exception as e:
            logger.error(f"Error generating lead response: {e}")
            return None
    
    def _invoke_claude_for_draft(
        self,
        action_file: Path,
        draft_type: str,
        platform: Optional[str] = None,
    ) -> Optional[str]:
        """
        Invoke Claude Code to generate draft content
        
        This uses Claude Code's reasoning capabilities to:
        1. Read the action file
        2. Apply Company Handbook rules
        3. Generate appropriate draft response
        """
        try:
            # Build Claude Code command
            cmd = [
                "claude",
                "--verbose",
                f"--prompt", self._build_draft_prompt(action_file, draft_type, platform),
            ]
            
            # Run Claude Code (capture output)
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=120,  # 2 minute timeout
            )
            
            if result.returncode != 0:
                logger.error(f"Claude Code failed: {result.stderr}")
                return None
            
            return result.stdout
            
        except subprocess.TimeoutExpired:
            logger.error("Claude Code timed out generating draft")
            return None
        except Exception as e:
            logger.error(f"Error invoking Claude Code: {e}")
            return None
    
    def _build_draft_prompt(self, action_file: Path, draft_type: str, platform: Optional[str] = None) -> str:
        """Build prompt for Claude Code to generate draft"""
        
        prompts = {
            "email": f"""
Read the email action file at {action_file} and generate a draft reply.

Rules from Company Handbook:
- Be professional and courteous
- Response time target: < 24 hours
- Include relevant pricing information if requested
- Flag any payment over $500 for approval
- Never commit to deadlines without approval

Generate a complete draft email that I can review and approve.
Format the draft with frontmatter including:
- type: email_draft
- in_reply_to: [original email ID]
- status: pending_review

Output ONLY the draft email content.
""",
            
            "social": f"""
Read the social media action file at {action_file} and generate a draft {platform} response.

Rules from Company Handbook:
- Be engaging but professional
- Respond to all mentions within 2 hours
- Handle complaints with empathy
- Never discuss pricing publicly (offer to DM)
- Max 280 characters for Twitter

Generate a complete draft response for {platform}.
Format with frontmatter including:
- type: social_draft
- platform: {platform}
- status: pending_review

Output ONLY the draft content.
""",
            
            "invoice": f"""
Read the action file at {action_file} and generate a draft invoice.

Rules from Company Handbook:
- Include all required fields (customer, amount, description, due date)
- Standard payment terms: Net 30
- Flag invoices over $1000 for approval
- Use company standard template

Generate a complete draft invoice in JSON format.
Format with frontmatter including:
- type: invoice_draft
- status: pending_review

Output ONLY the draft invoice content.
""",
            
            "lead_response": f"""
Read the lead action file at {action_file} and generate a prioritized response.

Rules from Company Handbook:
- High-value leads get response within 1 hour
- Include personalized greeting
- Offer demo/consultation
- Attach relevant pricing/proposal info
- Schedule follow-up in 48 hours if no response

Generate a complete lead response with:
1. Personalized email draft
2. Research on sender/company
3. Suggested next steps
4. Follow-up schedule

Format with frontmatter including:
- type: lead_response
- priority: high
- status: pending_review

Output ONLY the draft content.
""",
        }
        
        return prompts.get(draft_type, f"Generate draft for {action_file}")
    
    def _save_draft(self, draft: Draft) -> Path:
        """Save draft to Plans directory"""
        plans_dir = self.config.full_plans_path / "drafts"
        plans_dir.mkdir(parents=True, exist_ok=True)
        
        timestamp = draft.created.strftime("%Y%m%d_%H%M%S")
        filename = f"DRAFT_{draft.type}_{draft.id}_{timestamp}.md"
        filepath = plans_dir / filename
        
        filepath.write_text(draft.content, encoding='utf-8')
        
        logger.info(f"Saved draft to {filepath}")
        return filepath
    
    def create_approval_file(self, draft: Draft) -> Path:
        """
        Create approval request file in /Pending_Approval/
        
        This is the file that Local Agent will review and approve/reject
        """
        approval_dir = self.config.full_pending_approval_path
        approval_dir.mkdir(parents=True, exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"APPROVAL_{draft.type}_{draft.id}_{timestamp}.md"
        filepath = approval_dir / filename
        
        # Extract action details from draft
        action_type = draft.metadata.get("action_type", "unknown")
        
        content = f"""---
type: approval_request
action: {action_type}
draft_id: {draft.id}
created: {datetime.now().isoformat()}
expires: {draft.expires.isoformat()}
status: pending
cloud_generated: true
---

# Action Required: {action_type.replace('_', ' ').title()}

**Draft ID:** {draft.id}
**Created:** {datetime.now().strftime('%Y-%m-%d %H:%M')}
**Expires:** {draft.expires.strftime('%Y-%m-%d %H:%M')}
**Generated by:** Cloud Agent

## Draft Content

{draft.content}

## To Approve

1. Review the draft content above
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
        
        filepath.write_text(content, encoding='utf-8')
        
        logger.info(f"Created approval file: {filepath}")
        return filepath
    
    def cleanup_expired_drafts(self) -> int:
        """Remove expired drafts"""
        now = datetime.now()
        expired = [d for d in self.drafts if d.expires < now]
        
        for draft in expired:
            draft.status = "expired"
        
        self.drafts = [d for d in self.drafts if d.status != "expired"]
        
        logger.info(f"Cleaned up {len(expired)} expired drafts")
        return len(expired)
    
    def get_pending_drafts(self) -> List[Draft]:
        """Get all pending drafts"""
        return [d for d in self.drafts if d.status == "pending"]
    
    def get_draft_count(self) -> Dict[str, int]:
        """Get draft statistics"""
        return {
            "total": len(self.drafts),
            "pending": len([d for d in self.drafts if d.status == "pending"]),
            "approved": len([d for d in self.drafts if d.status == "approved"]),
            "rejected": len([d for d in self.drafts if d.status == "rejected"]),
            "expired": len([d for d in self.drafts if d.status == "expired"]),
        }
    
    def process_all_action_files(self) -> int:
        """
        Scan /Needs_Action/ and generate drafts for all items
        
        Returns number of drafts created
        """
        drafts_created = 0
        needs_action = self.config.full_needs_action_path
        
        if not needs_action.exists():
            return 0
        
        # Scan all action files
        for source_dir in needs_action.iterdir():
            if not source_dir.is_dir():
                continue
            
            for action_file in source_dir.iterdir():
                if not action_file.name.endswith('.md'):
                    continue
                
                # Check if already has draft
                draft_exists = self._check_draft_exists(action_file)
                if draft_exists:
                    continue
                
                # Determine draft type and generate
                draft = self._generate_appropriate_draft(action_file)
                if draft:
                    drafts_created += 1
        
        return drafts_created
    
    def _check_draft_exists(self, action_file: Path) -> bool:
        """Check if draft already exists for action file"""
        plans_dir = self.config.full_plans_path / "drafts"
        if not plans_dir.exists():
            return False
        
        # Check for existing draft
        for draft_file in plans_dir.iterdir():
            if action_file.stem in draft_file.name:
                return True
        return False
    
    def _generate_appropriate_draft(self, action_file: Path) -> Optional[Draft]:
        """Determine draft type and generate"""
        content = action_file.read_text(encoding='utf-8').lower()
        
        # Determine type from content
        if "email" in content or "gmail" in action_file.name.lower():
            return self.generate_email_draft(action_file)
        elif "twitter" in content or "tweet" in content:
            return self.generate_social_draft(action_file, "twitter")
        elif "facebook" in content:
            return self.generate_social_draft(action_file, "facebook")
        elif "instagram" in content:
            return self.generate_social_draft(action_file, "instagram")
        elif "linkedin" in content:
            return self.generate_social_draft(action_file, "linkedin")
        elif "invoice" in content or "payment" in content:
            return self.generate_invoice_draft(action_file)
        elif "lead" in content:
            return self.generate_lead_response(action_file)
        
        return None


def create_drafter(config: Optional[CloudConfig] = None) -> CloudDrafter:
    """Create CloudDrafter instance"""
    return CloudDrafter(config)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    config = get_config()
    drafter = create_drafter(config)
    
    # Process all action files
    count = drafter.process_all_action_files()
    logger.info(f"Created {count} drafts")
    
    # Show statistics
    stats = drafter.get_draft_count()
    logger.info(f"Draft stats: {stats}")
