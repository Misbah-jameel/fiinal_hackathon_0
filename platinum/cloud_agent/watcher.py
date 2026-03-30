"""
Cloud Watchers

These watchers run on the Cloud VM 24/7 and monitor:
- Gmail: Email triage and draft replies
- Social Media: Twitter, Facebook, Instagram, LinkedIn monitoring
- Lead Capture: Keywords indicating potential business opportunities

All actions are DRAFT-ONLY. Execution requires Local Agent approval.
"""

import logging
import time
from pathlib import Path
from datetime import datetime
from abc import ABC, abstractmethod
from typing import List, Dict, Optional, Any
from dataclasses import dataclass, field
import json
import hashlib

from .config import CloudConfig, get_config

logger = logging.getLogger(__name__)


@dataclass
class WatcherItem:
    """Represents an item detected by a watcher"""
    id: str
    type: str  # email, social_comment, lead, etc.
    source: str  # gmail, twitter, facebook, etc.
    content: str
    metadata: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)
    priority: str = "P3"  # P1=critical, P2=high, P3=normal, P4=low
    processed: bool = False


class BaseCloudWatcher(ABC):
    """Base class for all Cloud Watchers"""
    
    def __init__(self, config: Optional[CloudConfig] = None, check_interval: int = 300):
        self.config = config or get_config()
        self.check_interval = check_interval
        self.processed_ids: set = set()
        self.error_count: int = 0
        self.last_success: Optional[datetime] = None
        self.last_error: Optional[Exception] = None
        self.circuit_breaker_open: bool = False
        self.circuit_breaker_time: Optional[datetime] = None
        
    @abstractmethod
    def check_for_updates(self) -> List[WatcherItem]:
        """Check for new items. Override in subclass."""
        pass
    
    @abstractmethod
    def get_name(self) -> str:
        """Return watcher name. Override in subclass."""
        pass
    
    def create_action_file(self, item: WatcherItem) -> Path:
        """Create action file in Needs_Action/<source>/"""
        # Create source-specific subdirectory
        source_dir = self.config.full_needs_action_path / item.source
        source_dir.mkdir(parents=True, exist_ok=True)
        
        # Generate unique filename
        timestamp = item.timestamp.strftime("%Y%m%d_%H%M%S")
        filename = f"{item.type.upper()}_{item.id}_{timestamp}.md"
        filepath = source_dir / filename
        
        # Create markdown content
        content = self._generate_markdown(item)
        filepath.write_text(content, encoding="utf-8")
        
        logger.info(f"Created action file: {filepath}")
        return filepath
    
    def _generate_markdown(self, item: WatcherItem) -> str:
        """Generate markdown content for action file"""
        metadata_yaml = "\n".join([f"{k}: {v}" for k, v in item.metadata.items()])
        
        return f"""---
type: {item.type}
source: {item.source}
item_id: {item.id}
received: {item.timestamp.isoformat()}
priority: {item.priority}
status: pending
cloud_processed: {datetime.now().isoformat()}
---

# {item.type.replace('_', ' ').title()} — Action Required

**Source:** {item.source}
**Received:** {item.timestamp.strftime('%Y-%m-%d %H:%M')}
**Priority:** {item.priority}

## Content

{item.content}

## Suggested Actions

<!-- Cloud Agent: Generate draft response/action here -->
<!-- Local Agent: Review and move to /Pending_Approval/ for execution -->

## Metadata

```yaml
{metadata_yaml}
```

---
*Created by Cloud Agent ({self.get_name()})*
*Draft only — requires Local Agent approval for execution*
"""
    
    def should_process(self, item_id: str) -> bool:
        """Check if item should be processed (not already processed)"""
        return item_id not in self.processed_ids
    
    def mark_processed(self, item_id: str):
        """Mark item as processed"""
        self.processed_ids.add(item_id)
        # Keep only last 1000 IDs to prevent memory growth
        if len(self.processed_ids) > 1000:
            self.processed_ids = set(list(self.processed_ids)[-1000:])
    
    def check_circuit_breaker(self) -> bool:
        """Check if circuit breaker allows operation"""
        if not self.circuit_breaker_open:
            return True
        
        # Check if timeout has passed
        if self.circuit_breaker_time:
            elapsed = (datetime.now() - self.circuit_breaker_time).total_seconds()
            if elapsed >= self.config.circuit_breaker_timeout:
                logger.info(f"Circuit breaker reset for {self.get_name()}")
                self.circuit_breaker_open = False
                self.circuit_breaker_time = None
                return True
        return False
    
    def open_circuit_breaker(self):
        """Open circuit breaker (stop operations)"""
        self.circuit_breaker_open = True
        self.circuit_breaker_time = datetime.now()
        logger.warning(f"Circuit breaker opened for {self.get_name()}")
    
    def record_success(self):
        """Record successful operation"""
        self.error_count = 0
        self.last_success = datetime.now()
        if self.circuit_breaker_open:
            self.circuit_breaker_open = False
            self.circuit_breaker_time = None
    
    def record_error(self, error: Exception):
        """Record failed operation"""
        self.error_count += 1
        self.last_error = error
        self.last_success = None
        
        # Open circuit breaker after threshold
        if self.error_count >= self.config.circuit_breaker_threshold:
            self.open_circuit_breaker()
    
    def run(self, max_iterations: Optional[int] = None):
        """Run watcher loop"""
        logger.info(f"Starting {self.get_name()} (interval: {self.check_interval}s)")
        iteration = 0
        
        while max_iterations is None or iteration < max_iterations:
            try:
                if not self.check_circuit_breaker():
                    logger.debug(f"Circuit breaker open, skipping {self.get_name()}")
                    time.sleep(self.check_interval)
                    iteration += 1
                    continue
                
                items = self.check_for_updates()
                for item in items:
                    if self.should_process(item.id):
                        self.create_action_file(item)
                        self.mark_processed(item.id)
                
                self.record_success()
                
            except Exception as e:
                logger.error(f"Error in {self.get_name()}: {e}")
                self.record_error(e)
            
            time.sleep(self.check_interval)
            iteration += 1
        
        logger.info(f"Stopped {self.get_name()} after {iteration} iterations")
    
    def get_status(self) -> Dict[str, Any]:
        """Get watcher status"""
        return {
            "name": self.get_name(),
            "running": True,
            "processed_count": len(self.processed_ids),
            "error_count": self.error_count,
            "last_success": self.last_success.isoformat() if self.last_success else None,
            "last_error": str(self.last_error) if self.last_error else None,
            "circuit_breaker_open": self.circuit_breaker_open,
            "check_interval": self.check_interval,
        }


class GmailCloudWatcher(BaseCloudWatcher):
    """
    Gmail Cloud Watcher
    
    Monitors Gmail for:
    - Unread important emails
    - Emails from VIP contacts
    - Invoice/payment related emails
    
    Creates DRAFT replies only (no sending from Cloud)
    """
    
    def __init__(self, config: Optional[CloudConfig] = None):
        super().__init__(config, check_interval=config.gmail_check_interval if config else 120)
        self.vip_senders: List[str] = []  # Load from config or handbook
        self.keywords: List[str] = ["invoice", "payment", "urgent", "asap", "pricing"]
    
    def get_name(self) -> str:
        return "Gmail Cloud Watcher"
    
    def check_for_updates(self) -> List[WatcherItem]:
        """
        Check Gmail for new important emails
        
        In production, this would use Gmail API.
        For now, returns empty list (implement with actual API credentials)
        """
        # TODO: Implement Gmail API integration
        # from google.oauth2.credentials import Credentials
        # from googleapiclient.discovery import build
        
        logger.debug("Gmail Cloud Watcher checking for updates...")
        
        # Placeholder: In production, fetch from Gmail API
        # results = service.users().messages().list(userId='me', q='is:unread is:important').execute()
        
        return []
    
    def generate_draft_reply(self, item: WatcherItem) -> str:
        """Generate draft reply for email"""
        # This would be called by Claude Code via reasoning loop
        return f"""
---
type: email_draft
in_reply_to: {item.id}
draft_generated: {datetime.now().isoformat()}
status: pending_review
---

# Draft Reply

**To:** {item.metadata.get('from', 'Unknown')}
**Subject:** Re: {item.metadata.get('subject', 'No Subject')}

---

Dear {item.metadata.get('from_name', 'there')},

Thank you for your email. 

[Cloud Agent: Please generate appropriate response based on email content and Company Handbook rules]

Best regards,
AI Employee

---
*Draft generated by Cloud Agent — requires Local Agent review before sending*
"""


class SocialMediaCloudWatcher(BaseCloudWatcher):
    """
    Social Media Cloud Watcher
    
    Monitors:
    - Twitter/X mentions and DMs
    - Facebook Page comments and messages
    - Instagram Business comments
    - LinkedIn notifications
    
    Creates DRAFT responses only (no posting from Cloud)
    """
    
    def __init__(self, config: Optional[CloudConfig] = None):
        super().__init__(config, check_interval=config.social_check_interval if config else 300)
        self.platforms: List[str] = ["twitter", "facebook", "instagram", "linkedin"]
        self.lead_keywords: List[str] = ["pricing", "quote", "interested", "buy", "purchase", "demo"]
    
    def get_name(self) -> str:
        return "Social Media Cloud Watcher"
    
    def check_for_updates(self) -> List[WatcherItem]:
        """Check all social platforms for new items"""
        items = []
        
        for platform in self.platforms:
            try:
                platform_items = self._check_platform(platform)
                items.extend(platform_items)
            except Exception as e:
                logger.error(f"Error checking {platform}: {e}")
        
        return items
    
    def _check_platform(self, platform: str) -> List[WatcherItem]:
        """Check specific platform for updates"""
        # TODO: Implement platform-specific API integration
        logger.debug(f"Checking {platform} for updates...")
        
        # Placeholder: In production, fetch from respective APIs
        return []
    
    def is_lead(self, content: str) -> bool:
        """Check if content indicates a business lead"""
        content_lower = content.lower()
        return any(keyword in content_lower for keyword in self.lead_keywords)
    
    def generate_draft_response(self, item: WatcherItem) -> str:
        """Generate draft response for social media item"""
        if item.source == "twitter":
            return self._generate_twitter_draft(item)
        elif item.source == "facebook":
            return self._generate_facebook_draft(item)
        elif item.source == "instagram":
            return self._generate_instagram_draft(item)
        elif item.source == "linkedin":
            return self._generate_linkedin_draft(item)
        else:
            return f"# Draft response for {item.source}\n\n[Content to be generated]"
    
    def _generate_twitter_draft(self, item: WatcherItem) -> str:
        return f"""
---
type: social_draft
platform: twitter
in_reply_to: {item.id}
draft_generated: {datetime.now().isoformat()}
status: pending_review
---

# Draft Tweet Reply

**In Reply To:** @{item.metadata.get('username', 'unknown')}
**Original Tweet:** {item.content[:100]}...

---

[Cloud Agent: Generate appropriate response, max 280 characters]

---
*Draft generated by Cloud Agent — requires Local Agent review before posting*
"""
    
    def _generate_facebook_draft(self, item: WatcherItem) -> str:
        return f"""
---
type: social_draft
platform: facebook
in_reply_to: {item.id}
draft_generated: {datetime.now().isoformat()}
status: pending_review
---

# Draft Facebook Response

**Post ID:** {item.id}
**From:** {item.metadata.get('from', 'Unknown')}

---

[Cloud Agent: Generate appropriate response based on Company Handbook rules]

---
*Draft generated by Cloud Agent — requires Local Agent review before posting*
"""
    
    def _generate_instagram_draft(self, item: WatcherItem) -> str:
        return f"""
---
type: social_draft
platform: instagram
in_reply_to: {item.id}
draft_generated: {datetime.now().isoformat()}
status: pending_review
---

# Draft Instagram Response

**Media ID:** {item.id}
**From:** @{item.metadata.get('username', 'unknown')}

---

[Cloud Agent: Generate appropriate response with emoji if suitable]

---
*Draft generated by Cloud Agent — requires Local Agent review before posting*
"""
    
    def _generate_linkedin_draft(self, item: WatcherItem) -> str:
        return f"""
---
type: social_draft
platform: linkedin
in_reply_to: {item.id}
draft_generated: {datetime.now().isoformat()}
status: pending_review
---

# Draft LinkedIn Response

**Post ID:** {item.id}
**From:** {item.metadata.get('from', 'Unknown')}

---

[Cloud Agent: Generate professional response appropriate for LinkedIn]

---
*Draft generated by Cloud Agent — requires Local Agent review before posting*
"""


class LeadCaptureWatcher(BaseCloudWatcher):
    """
    Lead Capture Watcher
    
    Monitors all channels for business leads:
    - Pricing inquiries
    - Demo requests
    - Purchase intent signals
    - Partnership opportunities
    
    Prioritizes and creates high-priority action files
    """
    
    def __init__(self, config: Optional[CloudConfig] = None):
        super().__init__(config, check_interval=config.lead_check_interval if config else 300)
        self.high_value_keywords: List[str] = ["enterprise", "bulk", "annual", "contract", "partnership"]
    
    def get_name(self) -> str:
        return "Lead Capture Watcher"
    
    def check_for_updates(self) -> List[WatcherItem]:
        """
        Scan Needs_Action for new items and identify leads
        
        This watcher works by scanning existing action files
        and flagging potential leads for follow-up
        """
        leads = []
        
        # Scan Needs_Action directory for new items
        needs_action_dir = self.config.full_needs_action_path
        
        if not needs_action_dir.exists():
            return leads
        
        # Check each source subdirectory
        for source_dir in needs_action_dir.iterdir():
            if not source_dir.is_dir():
                continue
            
            for action_file in source_dir.iterdir():
                if not action_file.name.endswith('.md'):
                    continue
                
                # Check if already processed
                file_hash = hashlib.md5(str(action_file).encode()).hexdigest()[:8]
                if file_hash in self.processed_ids:
                    continue
                
                # Analyze for lead potential
                lead_item = self._analyze_for_lead(action_file, source_dir.name)
                if lead_item:
                    leads.append(lead_item)
                    self.mark_processed(file_hash)
        
        return leads
    
    def _analyze_for_lead(self, filepath: Path, source: str) -> Optional[WatcherItem]:
        """Analyze file for lead indicators"""
        try:
            content = filepath.read_text(encoding='utf-8')
            content_lower = content.lower()
            
            # Check for high-value keywords
            is_high_value = any(kw in content_lower for kw in self.high_value_keywords)
            
            # Check for lead keywords
            lead_keywords = ["pricing", "quote", "buy", "purchase", "demo", "interested"]
            is_lead = any(kw in content_lower for kw in lead_keywords)
            
            if not is_lead:
                return None
            
            # Determine priority
            priority = "P1" if is_high_value else "P2"
            
            return WatcherItem(
                id=f"lead_{filepath.stem}",
                type="business_lead",
                source=source,
                content=f"Potential business lead detected in {filepath.name}",
                metadata={
                    "original_file": str(filepath),
                    "is_high_value": is_high_value,
                    "source_file": filepath.name,
                },
                priority=priority,
            )
            
        except Exception as e:
            logger.error(f"Error analyzing {filepath}: {e}")
            return None
    
    def create_lead_action_file(self, item: WatcherItem) -> Path:
        """Create prioritized lead action file"""
        # Put leads in a special subdirectory
        leads_dir = self.config.full_needs_action_path / "leads"
        leads_dir.mkdir(parents=True, exist_ok=True)
        
        timestamp = item.timestamp.strftime("%Y%m%d_%H%M%S")
        filename = f"LEAD_{item.id}_{timestamp}.md"
        filepath = leads_dir / filename
        
        content = f"""---
type: business_lead
item_id: {item.id}
source: {item.source}
received: {item.timestamp.isoformat()}
priority: {item.priority}
status: pending
high_value: {item.metadata.get('is_high_value', False)}
---

# 🎯 Business Lead Detected

**Priority:** {item.priority}
**Source:** {item.source}
**Detected:** {item.timestamp.strftime('%Y-%m-%d %H:%M')}

## Lead Details

{item.content}

## Original Context

See: `{item.metadata.get('source_file', 'Unknown')}`

## Suggested Actions

1. [ ] Generate personalized response draft
2. [ ] Research sender/company
3. [ ] Prepare pricing/proposal information
4. [ ] Move to /Pending_Approval/ for Local Agent review
5. [ ] Schedule follow-up if no response in 48 hours

## Notes

<!-- Cloud Agent: Add research and draft response here -->

---
*High-priority lead detected by Cloud Agent*
*Requires immediate Local Agent attention*
"""
        
        filepath.write_text(content, encoding='utf-8')
        logger.info(f"Created lead action file: {filepath}")
        return filepath


def create_all_cloud_watchers(config: Optional[CloudConfig] = None) -> List[BaseCloudWatcher]:
    """Create all cloud watchers"""
    return [
        GmailCloudWatcher(config),
        SocialMediaCloudWatcher(config),
        LeadCaptureWatcher(config),
    ]


def start_all_watchers(config: Optional[CloudConfig] = None, max_iterations: Optional[int] = None):
    """Start all cloud watchers in parallel"""
    import threading
    
    watchers = create_all_cloud_watchers(config)
    threads = []
    
    for watcher in watchers:
        thread = threading.Thread(target=watcher.run, args=(max_iterations,), daemon=True)
        threads.append(thread)
        thread.start()
        logger.info(f"Started {watcher.get_name()} in thread {thread.ident}")
    
    return threads


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    # Test watchers
    config = get_config()
    threads = start_all_watchers(config, max_iterations=10)
    
    # Wait for all threads
    for thread in threads:
        thread.join()
