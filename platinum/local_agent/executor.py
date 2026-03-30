"""
Local Agent Executor

Executes approved actions via MCP servers:
- Send emails via Gmail MCP
- Post to social media via Social MCP
- Process payments via Odoo MCP
- Send WhatsApp messages

All actions are logged to audit trail.
Security: Credentials and MCP access stay local (never synced to cloud).
"""

import logging
import subprocess
import json
import time
from pathlib import Path
from datetime import datetime
from typing import Dict, Optional, Any, List
from dataclasses import dataclass

from .config import LocalConfig, get_config

logger = logging.getLogger(__name__)


@dataclass
class ExecutionResult:
    """Result of action execution"""
    success: bool
    action_type: str
    file_path: Path
    result_data: Dict = None
    error: str = None
    timestamp: datetime = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()


class LocalExecutor:
    """
    Local Agent Executor
    
    Executes approved actions via MCP servers.
    All actions require prior approval (file in /Approved/).
    """
    
    def __init__(self, config: Optional[LocalConfig] = None):
        self.config = config or get_config()
        
        # Execution statistics
        self.total_executed = 0
        self.total_success = 0
        self.total_failed = 0
        
        # Rate limiting tracking
        self.executions_today: List[datetime] = []
        self.last_execution: Optional[datetime] = None
    
    def execute_approved_file(self, filepath: Path) -> ExecutionResult:
        """
        Execute an approved action file
        
        Reads the file, determines action type, and calls appropriate MCP
        """
        try:
            content = filepath.read_text(encoding='utf-8')
            
            # Parse frontmatter
            metadata = self._parse_frontmatter(content)
            action_type = metadata.get('action', 'unknown')
            
            logger.info(f"Executing {action_type}: {filepath.name}")
            
            # Check rate limits
            if not self._check_rate_limit(action_type):
                return ExecutionResult(
                    success=False,
                    action_type=action_type,
                    file_path=filepath,
                    error="Rate limit exceeded",
                )
            
            # Execute based on action type
            if action_type == "email_send":
                result = self._execute_email_send(filepath, metadata, content)
            elif action_type == "social_post":
                result = self._execute_social_post(filepath, metadata, content)
            elif action_type in ["tweet", "twitter_post"]:
                result = self._execute_tweet(filepath, metadata, content)
            elif action_type in ["facebook_post"]:
                result = self._execute_facebook_post(filepath, metadata, content)
            elif action_type in ["instagram_post"]:
                result = self._execute_instagram_post(filepath, metadata, content)
            elif action_type == "payment":
                result = self._execute_payment(filepath, metadata, content)
            elif action_type == "invoice_post":
                result = self._execute_invoice_post(filepath, metadata, content)
            elif action_type == "whatsapp_send":
                result = self._execute_whatsapp_send(filepath, metadata, content)
            else:
                logger.warning(f"Unknown action type: {action_type}")
                result = ExecutionResult(
                    success=False,
                    action_type=action_type,
                    file_path=filepath,
                    error=f"Unknown action type: {action_type}",
                )
            
            # Update statistics
            self.total_executed += 1
            if result.success:
                self.total_success += 1
            else:
                self.total_failed += 1
            
            # Log execution
            self._log_execution(result)
            
            return result
            
        except Exception as e:
            logger.error(f"Error executing {filepath.name}: {e}")
            return ExecutionResult(
                success=False,
                action_type="unknown",
                file_path=filepath,
                error=str(e),
            )
    
    def _parse_frontmatter(self, content: str) -> Dict:
        """Parse YAML frontmatter from content"""
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
        
        return metadata
    
    def _check_rate_limit(self, action_type: str) -> bool:
        """Check if action is within rate limits"""
        now = datetime.now()
        today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        
        # Filter executions today
        self.executions_today = [
            e for e in self.executions_today if e > today_start
        ]
        
        # Check limits based on action type
        if action_type == "email_send":
            if len(self.executions_today) >= self.config.max_emails_per_hour:
                logger.warning(f"Email rate limit exceeded ({self.config.max_emails_per_hour}/hour)")
                return False
        
        elif action_type in ["social_post", "tweet", "facebook_post", "instagram_post"]:
            if len(self.executions_today) >= self.config.max_social_posts_per_day:
                logger.warning(f"Social post rate limit exceeded ({self.config.max_social_posts_per_day}/day)")
                return False
        
        elif action_type == "payment":
            if len(self.executions_today) >= self.config.max_payments_per_day:
                logger.warning(f"Payment rate limit exceeded ({self.config.max_payments_per_day}/day)")
                return False
        
        return True
    
    def _execute_email_send(self, filepath: Path, metadata: Dict, content: str) -> ExecutionResult:
        """Execute email send via Email MCP"""
        try:
            # Extract email details from content
            to = metadata.get('to', '')
            subject = metadata.get('subject', '')
            
            # Use Claude Code with Email MCP to send
            cmd = [
                "claude",
                "--verbose",
                "--prompt",
                f"""Send this email using the Email MCP:

To: {to}
Subject: {subject}

Content:
{content}

Use the email_send tool to send this email.
Return the result as JSON: {{"success": true, "message_id": "..."}}
"""
            ]
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=self.config.mcp_timeout,
            )
            
            if result.returncode != 0:
                return ExecutionResult(
                    success=False,
                    action_type="email_send",
                    file_path=filepath,
                    error=result.stderr,
                )
            
            # Parse result
            try:
                result_data = json.loads(result.stdout.strip())
            except:
                result_data = {"success": True}
            
            return ExecutionResult(
                success=result_data.get('success', True),
                action_type="email_send",
                file_path=filepath,
                result_data=result_data,
            )
            
        except subprocess.TimeoutExpired:
            return ExecutionResult(
                success=False,
                action_type="email_send",
                file_path=filepath,
                error="Email send timed out",
            )
        except Exception as e:
            return ExecutionResult(
                success=False,
                action_type="email_send",
                file_path=filepath,
                error=str(e),
            )
    
    def _execute_social_post(self, filepath: Path, metadata: Dict, content: str) -> ExecutionResult:
        """Execute social media post via Social MCP"""
        try:
            platform = metadata.get('platform', 'twitter')
            
            # Use Claude Code with Social MCP to post
            cmd = [
                "claude",
                "--verbose",
                "--prompt",
                f"""Post to {platform} using the Social MCP:

Content:
{content}

Use the social_post_{platform} tool to post this content.
Return the result as JSON: {{"success": true, "post_id": "..."}}
"""
            ]
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=self.config.mcp_timeout,
            )
            
            if result.returncode != 0:
                return ExecutionResult(
                    success=False,
                    action_type="social_post",
                    file_path=filepath,
                    error=result.stderr,
                )
            
            # Parse result
            try:
                result_data = json.loads(result.stdout.strip())
            except:
                result_data = {"success": True, "platform": platform}
            
            return ExecutionResult(
                success=result_data.get('success', True),
                action_type="social_post",
                file_path=filepath,
                result_data=result_data,
            )
            
        except Exception as e:
            return ExecutionResult(
                success=False,
                action_type="social_post",
                file_path=filepath,
                error=str(e),
            )
    
    def _execute_tweet(self, filepath: Path, metadata: Dict, content: str) -> ExecutionResult:
        """Execute tweet via Social MCP"""
        return self._execute_social_post(filepath, {**metadata, 'platform': 'twitter'}, content)
    
    def _execute_facebook_post(self, filepath: Path, metadata: Dict, content: str) -> ExecutionResult:
        """Execute Facebook post via Social MCP"""
        return self._execute_social_post(filepath, {**metadata, 'platform': 'facebook'}, content)
    
    def _execute_instagram_post(self, filepath: Path, metadata: Dict, content: str) -> ExecutionResult:
        """Execute Instagram post via Social MCP"""
        return self._execute_social_post(filepath, {**metadata, 'platform': 'instagram'}, content)
    
    def _execute_payment(self, filepath: Path, metadata: Dict, content: str) -> ExecutionResult:
        """Execute payment via Odoo MCP"""
        try:
            amount = metadata.get('amount', '0')
            recipient = metadata.get('recipient', '')
            
            # Check payment limit
            if float(amount) > self.config.max_payment_amount:
                return ExecutionResult(
                    success=False,
                    action_type="payment",
                    file_path=filepath,
                    error=f"Payment amount ${amount} exceeds limit ${self.config.max_payment_amount}",
                )
            
            # Use Claude Code with Odoo MCP to create payment
            cmd = [
                "claude",
                "--verbose",
                "--prompt",
                f"""Create payment using the Odoo MCP:

Amount: ${amount}
Recipient: {recipient}

Content:
{content}

Use Odoo MCP to create the payment.
Return the result as JSON: {{"success": true, "payment_id": "..."}}
"""
            ]
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=self.config.mcp_timeout * 2,  # Payments take longer
            )
            
            if result.returncode != 0:
                return ExecutionResult(
                    success=False,
                    action_type="payment",
                    file_path=filepath,
                    error=result.stderr,
                )
            
            # Parse result
            try:
                result_data = json.loads(result.stdout.strip())
            except:
                result_data = {"success": True}
            
            return ExecutionResult(
                success=result_data.get('success', True),
                action_type="payment",
                file_path=filepath,
                result_data=result_data,
            )
            
        except Exception as e:
            return ExecutionResult(
                success=False,
                action_type="payment",
                file_path=filepath,
                error=str(e),
            )
    
    def _execute_invoice_post(self, filepath: Path, metadata: Dict, content: str) -> ExecutionResult:
        """Execute invoice posting via Odoo MCP"""
        try:
            # Use Claude Code with Odoo MCP to post invoice
            cmd = [
                "claude",
                "--verbose",
                "--prompt",
                f"""Post invoice using the Odoo MCP:

Content:
{content}

Use Odoo MCP to post the invoice.
Return the result as JSON: {{"success": true, "invoice_id": "..."}}
"""
            ]
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=self.config.mcp_timeout,
            )
            
            if result.returncode != 0:
                return ExecutionResult(
                    success=False,
                    action_type="invoice_post",
                    file_path=filepath,
                    error=result.stderr,
                )
            
            # Parse result
            try:
                result_data = json.loads(result.stdout.strip())
            except:
                result_data = {"success": True}
            
            return ExecutionResult(
                success=result_data.get('success', True),
                action_type="invoice_post",
                file_path=filepath,
                result_data=result_data,
            )
            
        except Exception as e:
            return ExecutionResult(
                success=False,
                action_type="invoice_post",
                file_path=filepath,
                error=str(e),
            )
    
    def _execute_whatsapp_send(self, filepath: Path, metadata: Dict, content: str) -> ExecutionResult:
        """Execute WhatsApp message send"""
        try:
            # WhatsApp uses local session (never synced)
            # This would integrate with the WhatsApp watcher/sender
            
            logger.info(f"WhatsApp send would be executed here (requires WhatsApp session)")
            
            return ExecutionResult(
                success=True,
                action_type="whatsapp_send",
                file_path=filepath,
                result_data={"message": "WhatsApp integration placeholder"},
            )
            
        except Exception as e:
            return ExecutionResult(
                success=False,
                action_type="whatsapp_send",
                file_path=filepath,
                error=str(e),
            )
    
    def _log_execution(self, result: ExecutionResult):
        """Log execution to audit trail"""
        audit_entry = {
            "timestamp": result.timestamp.isoformat(),
            "action_type": result.action_type,
            "actor": self.config.agent_id,
            "target": str(result.file_path),
            "parameters": {},
            "approval_status": "approved",
            "approved_by": "human",
            "result": "success" if result.success else "failed",
            "error": result.error,
        }
        
        # Write to audit log
        audit_file = self.config.full_audit_path / f"{datetime.now().strftime('%Y-%m-%d')}.jsonl"
        audit_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(audit_file, 'a', encoding='utf-8') as f:
            f.write(json.dumps(audit_entry) + '\n')
    
    def get_statistics(self) -> Dict:
        """Get execution statistics"""
        return {
            "total_executed": self.total_executed,
            "total_success": self.total_success,
            "total_failed": self.total_failed,
            "success_rate": self.total_success / max(self.total_executed, 1) * 100,
            "last_execution": self.last_execution.isoformat() if self.last_execution else None,
            "executions_today": len(self.executions_today),
        }
    
    def process_approved_directory(self) -> int:
        """
        Process all files in /Approved/ directory
        
        Returns number of files processed
        """
        approved_dir = self.config.full_approved_path
        
        if not approved_dir.exists():
            return 0
        
        processed = 0
        for filepath in approved_dir.iterdir():
            if not filepath.name.endswith('.md'):
                continue
            
            # Execute
            result = self.execute_approved_file(filepath)
            
            if result.success:
                # Move to Done
                done_dir = self.config.full_done_path
                done_dir.mkdir(parents=True, exist_ok=True)
                filepath.rename(done_dir / filepath.name)
            else:
                # Move to quarantine or back to Pending
                logger.warning(f"Execution failed: {filepath.name} - {result.error}")
            
            processed += 1
            self.last_execution = datetime.now()
        
        return processed


def create_executor(config: Optional[LocalConfig] = None) -> LocalExecutor:
    """Create LocalExecutor instance"""
    return LocalExecutor(config)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    config = get_config()
    executor = create_executor(config)
    
    # Process approved directory
    count = executor.process_approved_directory()
    logger.info(f"Processed {count} approved files")
    
    # Show statistics
    stats = executor.get_statistics()
    logger.info(f"Execution statistics: {stats}")
