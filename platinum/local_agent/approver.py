"""
Local Agent Approver

Handles human-in-the-loop approval workflow:
- Monitor /Pending_Approval/ for new approval requests
- Notify user of pending approvals
- Process user approval/rejection decisions
- Move approved files to /Approved/ for execution
"""

import logging
import time
import shutil
from pathlib import Path
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Callable
from dataclasses import dataclass
import json

from .config import LocalConfig, get_config

logger = logging.getLogger(__name__)


@dataclass
class ApprovalRequest:
    """Represents an approval request"""
    file_path: Path
    action_type: str
    created: datetime
    expires: datetime
    metadata: Dict
    status: str = "pending"  # pending, approved, rejected, expired
    content: str = ""
    
    @classmethod
    def from_file(cls, filepath: Path) -> Optional["ApprovalRequest"]:
        """Parse approval request from file"""
        try:
            content = filepath.read_text(encoding='utf-8')
            
            # Extract frontmatter
            if not content.startswith('---'):
                return None
            
            end_frontmatter = content.find('---', 3)
            if end_frontmatter == -1:
                return None
            
            frontmatter = content[4:end_frontmatter].strip()
            
            # Parse metadata
            metadata = {}
            for line in frontmatter.split('\n'):
                if ':' in line:
                    key, value = line.split(':', 1)
                    metadata[key.strip()] = value.strip()
            
            # Extract required fields
            action_type = metadata.get('action', 'unknown')
            created_str = metadata.get('created', datetime.now().isoformat())
            expires_str = metadata.get('expires', (datetime.now() + timedelta(hours=24)).isoformat())
            
            try:
                created = datetime.fromisoformat(created_str)
            except:
                created = datetime.now()
            
            try:
                expires = datetime.fromisoformat(expires_str)
            except:
                expires = datetime.now() + timedelta(hours=24)
            
            return cls(
                file_path=filepath,
                action_type=action_type,
                created=created,
                expires=expires,
                metadata=metadata,
                content=content,
            )
            
        except Exception as e:
            logger.error(f"Error parsing approval file {filepath}: {e}")
            return None


class LocalApprover:
    """
    Local Agent Approver
    
    Manages human-in-the-loop approval workflow:
    1. Monitor /Pending_Approval/ for new requests
    2. Notify user (desktop, sound, email)
    3. Wait for user decision
    4. Move file to /Approved/ or /Rejected/
    """
    
    def __init__(self, config: Optional[LocalConfig] = None):
        self.config = config or get_config()
        self.pending_requests: List[ApprovalRequest] = []
        self.approval_callbacks: List[Callable] = []
        self.rejection_callbacks: List[Callable] = []
        
        # Statistics
        self.total_approved = 0
        self.total_rejected = 0
        self.total_expired = 0
    
    def check_pending_approvals(self) -> List[ApprovalRequest]:
        """Check /Pending_Approval/ for new approval requests"""
        approval_dir = self.config.full_pending_approval_path
        
        if not approval_dir.exists():
            return []
        
        requests = []
        for filepath in approval_dir.iterdir():
            if not filepath.name.endswith('.md'):
                continue
            
            # Check if already processed
            if self._is_already_processed(filepath):
                continue
            
            # Parse approval request
            request = ApprovalRequest.from_file(filepath)
            if request:
                # Check if expired
                if request.expires < datetime.now():
                    request.status = "expired"
                    self._handle_expired(request)
                    continue
                
                requests.append(request)
        
        self.pending_requests = requests
        return requests
    
    def _is_already_processed(self, filepath: Path) -> bool:
        """Check if approval file was already processed"""
        # Check Approved directory
        approved_dir = self.config.full_approved_path
        if approved_dir.exists() and (approved_dir / filepath.name).exists():
            return True
        
        # Check Rejected directory
        rejected_dir = self.config.full_vault_path / "Rejected"
        if rejected_dir.exists() and (rejected_dir / filepath.name).exists():
            return True
        
        return False
    
    def notify_user(self, requests: List[ApprovalRequest]):
        """Notify user of pending approvals"""
        if not requests:
            return
        
        logger.info(f"📋 {len(requests)} approval(s) pending")
        
        # Desktop notification
        if self.config.desktop_notifications:
            self._send_desktop_notification(requests)
        
        # Sound notification
        if self.config.notification_sound:
            self._play_notification_sound()
        
        # Email notification (if configured)
        if self.config.email_notifications and self.config.notification_email:
            self._send_email_notification(requests)
    
    def _send_desktop_notification(self, requests: List[ApprovalRequest]):
        """Send desktop notification"""
        try:
            # Cross-platform notification
            import sys
            
            if sys.platform == "win32":
                # Windows toast notification
                from win10toast import ToastNotifier
                toaster = ToastNotifier()
                toaster.show_toast(
                    "AI Employee - Approval Required",
                    f"{len(requests)} action(s) awaiting your approval",
                    duration=10,
                )
            elif sys.platform == "darwin":
                # macOS notification
                import subprocess
                title = "AI Employee - Approval Required"
                message = f"{len(requests)} action(s) awaiting your approval"
                subprocess.run([
                    "osascript",
                    "-e", f'display notification "{message}" with title "{title}"'
                ])
            elif sys.platform == "linux":
                # Linux notification
                import subprocess
                subprocess.run([
                    "notify-send",
                    "AI Employee - Approval Required",
                    f"{len(requests)} action(s) awaiting your approval"
                ])
            
            logger.debug("Desktop notification sent")
            
        except Exception as e:
            logger.debug(f"Desktop notification failed: {e}")
    
    def _play_notification_sound(self):
        """Play notification sound"""
        try:
            import sys
            import subprocess
            
            if sys.platform == "win32":
                import winsound
                winsound.PlaySound("SystemNotification", winsound.SND_ASYNC)
            elif sys.platform == "darwin":
                subprocess.run(["afplay", "/System/Library/Sounds/Glass.aiff"])
            elif sys.platform == "linux":
                subprocess.run(["paplay", "/usr/share/sounds/freedesktop/stereo/message.oga"])
            
            logger.debug("Notification sound played")
            
        except Exception as e:
            logger.debug(f"Notification sound failed: {e}")
    
    def _send_email_notification(self, requests: List[ApprovalRequest]):
        """Send email notification"""
        try:
            # This would use the email MCP to send notification
            # For now, just log
            logger.info(f"Email notification would be sent to {self.config.notification_email}")
            
        except Exception as e:
            logger.error(f"Email notification failed: {e}")
    
    def approve(self, request: ApprovalRequest) -> bool:
        """
        Approve an action
        
        Moves file from /Pending_Approval/ to /Approved/
        """
        try:
            approved_dir = self.config.full_approved_path
            approved_dir.mkdir(parents=True, exist_ok=True)
            
            # Move file
            target = approved_dir / request.file_path.name
            shutil.move(str(request.file_path), str(target))
            
            request.status = "approved"
            self.total_approved += 1
            
            logger.info(f"✅ Approved: {request.file_path.name}")
            
            # Trigger callbacks
            for callback in self.approval_callbacks:
                try:
                    callback(request)
                except Exception as e:
                    logger.error(f"Approval callback error: {e}")
            
            # Log approval
            self._log_action("approval", request, "approved")
            
            return True
            
        except Exception as e:
            logger.error(f"Error approving {request.file_path.name}: {e}")
            return False
    
    def reject(self, request: ApprovalRequest) -> bool:
        """
        Reject an action
        
        Moves file from /Pending_Approval/ to /Rejected/
        """
        try:
            rejected_dir = self.config.full_vault_path / "Rejected"
            rejected_dir.mkdir(parents=True, exist_ok=True)
            
            # Move file
            target = rejected_dir / request.file_path.name
            shutil.move(str(request.file_path), str(target))
            
            request.status = "rejected"
            self.total_rejected += 1
            
            logger.info(f"❌ Rejected: {request.file_path.name}")
            
            # Trigger callbacks
            for callback in self.rejection_callbacks:
                try:
                    callback(request)
                except Exception as e:
                    logger.error(f"Rejection callback error: {e}")
            
            # Log rejection
            self._log_action("approval", request, "rejected")
            
            return True
            
        except Exception as e:
            logger.error(f"Error rejecting {request.file_path.name}: {e}")
            return False
    
    def _handle_expired(self, request: ApprovalRequest):
        """Handle expired approval request"""
        try:
            # Move to Rejected with expired status
            rejected_dir = self.config.full_vault_path / "Rejected"
            rejected_dir.mkdir(parents=True, exist_ok=True)
            
            target = rejected_dir / f"EXPIRED_{request.file_path.name}"
            shutil.move(str(request.file_path), str(target))
            
            self.total_expired += 1
            
            logger.warning(f"⏰ Expired: {request.file_path.name}")
            
            # Log expiration
            self._log_action("approval", request, "expired")
            
        except Exception as e:
            logger.error(f"Error handling expired {request.file_path.name}: {e}")
    
    def _log_action(self, action_type: str, request: ApprovalRequest, outcome: str):
        """Log approval action to audit log"""
        audit_entry = {
            "timestamp": datetime.now().isoformat(),
            "action_type": action_type,
            "actor": self.config.agent_id,
            "target": str(request.file_path),
            "parameters": {
                "action": request.action_type,
                "metadata": request.metadata,
            },
            "approval_status": outcome,
            "approved_by": "human" if outcome == "approved" else "system" if outcome == "expired" else "human",
            "result": outcome,
        }
        
        # Write to audit log
        audit_file = self.config.full_audit_path / f"{datetime.now().strftime('%Y-%m-%d')}.jsonl"
        audit_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(audit_file, 'a', encoding='utf-8') as f:
            f.write(json.dumps(audit_entry) + '\n')
    
    def auto_approve_safe_actions(self) -> int:
        """
        Auto-approve safe actions (if configured)
        
        By default, auto-approve is disabled for safety
        """
        if self.config.auto_approve_threshold > 0:
            logger.warning("Auto-approve is enabled - review configuration!")
        
        approved_count = 0
        
        for request in self.pending_requests:
            # Check if eligible for auto-approve
            if self._is_safe_to_auto_approve(request):
                if self.approve(request):
                    approved_count += 1
        
        return approved_count
    
    def _is_safe_to_auto_approve(self, request: ApprovalRequest) -> bool:
        """Check if action is safe to auto-approve"""
        # Never auto-approve if threshold is 0 (default)
        if self.config.auto_approve_threshold <= 0:
            return False
        
        # Check amount
        amount = float(request.metadata.get('amount', 0))
        if amount > self.config.auto_approve_threshold:
            return False
        
        # Check action type
        safe_types = ["email_send", "social_post"]
        if request.action_type not in safe_types:
            return False
        
        # Check if from known contact
        # (would need contact list to verify)
        
        return True
    
    def get_statistics(self) -> Dict:
        """Get approval statistics"""
        return {
            "pending": len(self.pending_requests),
            "approved": self.total_approved,
            "rejected": self.total_rejected,
            "expired": self.total_expired,
            "auto_approve_enabled": self.config.auto_approve_threshold > 0,
            "auto_approve_threshold": self.config.auto_approve_threshold,
        }
    
    def run(self, check_interval: int = 30, max_iterations: Optional[int] = None):
        """
        Run approval monitoring loop
        
        Continuously checks for new approvals and notifies user
        """
        logger.info(f"Starting Local Approver (interval: {check_interval}s)")
        iteration = 0
        
        while max_iterations is None or iteration < max_iterations:
            try:
                # Check for new approvals
                requests = self.check_pending_approvals()
                
                if requests:
                    # Notify user
                    self.notify_user(requests)
                    
                    # Try auto-approve (if enabled)
                    auto_approved = self.auto_approve_safe_actions()
                    if auto_approved > 0:
                        logger.info(f"Auto-approved {auto_approved} safe actions")
                
                # Wait for next check
                time.sleep(check_interval)
                
            except Exception as e:
                logger.error(f"Approver loop error: {e}")
                time.sleep(check_interval)
            
            iteration += 1
        
        logger.info(f"Stopped Local Approver after {iteration} iterations")
    
    def register_approval_callback(self, callback: Callable):
        """Register callback for when approval is granted"""
        self.approval_callbacks.append(callback)
    
    def register_rejection_callback(self, callback: Callable):
        """Register callback for when approval is rejected"""
        self.rejection_callbacks.append(callback)


def create_approver(config: Optional[LocalConfig] = None) -> LocalApprover:
    """Create LocalApprover instance"""
    return LocalApprover(config)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    config = get_config()
    approver = create_approver(config)
    
    # Run approver
    approver.run(max_iterations=10)
    
    # Show statistics
    stats = approver.get_statistics()
    logger.info(f"Approval statistics: {stats}")
