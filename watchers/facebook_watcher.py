#!/usr/bin/env python3
"""
Facebook & Instagram Watcher — AI Employee Gold Tier
------------------------------------------------------
Monitors Facebook Page + Instagram Business Account for:
- Comments on posts
- Mentions
- DMs (via Messenger API)
- New followers (Instagram)

Creates action files in /Needs_Action for Claude to process.

Usage:
  python watchers/facebook_watcher.py --vault ./AI_Employee_Vault
  python watchers/facebook_watcher.py --vault ./AI_Employee_Vault --watch
  python watchers/facebook_watcher.py --vault ./AI_Employee_Vault --auth
  python watchers/facebook_watcher.py --vault ./AI_Employee_Vault --platform instagram
"""

import os
import sys
import json
import time
import argparse
import logging
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, List

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

try:
    import requests
    from requests.exceptions import RequestException, Timeout, HTTPError
    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False

sys.path.insert(0, str(Path(__file__).parent))
try:
    from base_watcher import BaseWatcher
except ImportError:
    class BaseWatcher:
        def __init__(self, vault_path, check_interval=300):
            self.vault_path = Path(vault_path)
            self.needs_action = self.vault_path / "Needs_Action"
            self.check_interval = check_interval
            self.logger = logging.getLogger(self.__class__.__name__)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(name)s] %(levelname)s: %(message)s"
)

GRAPH_API = "https://graph.facebook.com/v19.0"

# Error handling constants
MAX_RETRIES = 3
RETRY_DELAY = 5  # seconds
REQUEST_TIMEOUT = 30  # seconds


class FacebookInstagramWatcher(BaseWatcher):
    def __init__(self, vault_path: str, platform: str = "both"):
        super().__init__(vault_path, check_interval=300)

        self.platform = platform  # "facebook", "instagram", "both"
        self.fb_token = os.getenv("FACEBOOK_ACCESS_TOKEN", "")
        self.fb_page_id = os.getenv("FACEBOOK_PAGE_ID", "")
        self.ig_token = os.getenv("INSTAGRAM_ACCESS_TOKEN", "")
        self.ig_user_id = os.getenv("INSTAGRAM_USER_ID", "")

        self.processed_ids_file = self.vault_path / "Logs" / "facebook_processed.json"
        self.processed_ids = self._load_processed()
        
        # Error tracking
        self.consecutive_errors = 0
        self.last_success = None
        
        # Rate limiting
        self.api_calls = 0
        self.rate_limit_reset = time.time() + 3600  # Reset after 1 hour

    def _load_processed(self) -> set:
        if self.processed_ids_file.exists():
            try:
                return set(json.loads(self.processed_ids_file.read_text()))
            except Exception:
                pass
        return set()

    def _save_processed(self):
        self.processed_ids_file.parent.mkdir(parents=True, exist_ok=True)
        # Keep only last 1000 IDs to prevent file from growing too large
        self.processed_ids_file.write_text(
            json.dumps(list(self.processed_ids)[-1000:])
        )

    def _graph_get(self, endpoint: str, token: str, params: dict = None) -> dict:
        """Make Graph API request with retry logic and error handling."""
        url = f"{GRAPH_API}/{endpoint}"
        params = params or {}
        params["access_token"] = token
        
        for attempt in range(MAX_RETRIES):
            try:
                resp = requests.get(url, params=params, timeout=REQUEST_TIMEOUT)
                self.api_calls += 1
                
                # Check for rate limiting
                if resp.status_code == 429:
                    retry_after = int(resp.headers.get('Retry-After', RETRY_DELAY))
                    self.logger.warning(f"Rate limited. Waiting {retry_after}s...")
                    time.sleep(retry_after)
                    continue
                
                resp.raise_for_status()
                self.consecutive_errors = 0
                self.last_success = datetime.now()
                return resp.json()
                
            except Timeout:
                self.logger.warning(f"Request timeout (attempt {attempt+1}/{MAX_RETRIES})")
                time.sleep(RETRY_DELAY * (attempt + 1))
                
            except HTTPError as e:
                if resp.status_code == 401:
                    self.logger.error("Authentication failed. Check your access token.")
                    self.consecutive_errors += 1
                    return {"error": {"message": "Authentication failed", "type": "OAuthException"}}
                elif resp.status_code == 403:
                    self.logger.error("Permission denied. Check API permissions.")
                    self.consecutive_errors += 1
                    return {"error": {"message": "Permission denied", "type": "OAuthException"}}
                else:
                    self.logger.warning(f"HTTP error {resp.status_code} (attempt {attempt+1}/{MAX_RETRIES})")
                    time.sleep(RETRY_DELAY * (attempt + 1))
                    
            except RequestException as e:
                self.logger.error(f"Request failed: {e}")
                time.sleep(RETRY_DELAY * (attempt + 1))
        
        # All retries failed
        self.consecutive_errors += 1
        self.logger.error(f"Failed after {MAX_RETRIES} attempts")
        return {}

    def check_facebook(self) -> list:
        """Check Facebook Page for new comments and messages."""
        if not self.fb_token or not self.fb_page_id:
            self.logger.warning("FACEBOOK_ACCESS_TOKEN or FACEBOOK_PAGE_ID not set in .env")
            return []
        
        # Circuit breaker: stop if too many consecutive errors
        if self.consecutive_errors >= MAX_RETRIES:
            self.logger.error(f"Circuit breaker triggered: {self.consecutive_errors} consecutive errors")
            return []

        items = []

        try:
            # Get recent posts comments
            data = self._graph_get(
                f"{self.fb_page_id}/feed",
                self.fb_token,
                {"fields": "id,message,comments{from,message,created_time},created_time", "limit": 5}
            )

            if "error" in data:
                self.logger.error(f"Facebook API error: {data['error'].get('message', 'Unknown error')}")
                return []

            for post in data.get("data", []):
                for comment in post.get("comments", {}).get("data", []):
                    cid = comment.get("id", "")
                    if cid and cid not in self.processed_ids:
                        items.append({
                            "platform": "facebook",
                            "type": "comment",
                            "id": cid,
                            "post_id": post.get("id"),
                            "text": comment.get("message", ""),
                            "from": comment.get("from", {}).get("name", "unknown"),
                            "created_at": comment.get("created_time", "")
                        })
                        self.processed_ids.add(cid)

            # Get messages (Messenger)
            conversations = self._graph_get(
                f"{self.fb_page_id}/conversations",
                self.fb_token,
                {"fields": "messages{from,message,created_time}", "limit": 5}
            )
            
            if "data" in conversations:
                for conv in conversations["data"]:
                    for msg in conv.get("messages", {}).get("data", []):
                        mid = msg.get("id", "")
                        if mid and mid not in self.processed_ids:
                            items.append({
                                "platform": "facebook",
                                "type": "message",
                                "id": mid,
                                "text": msg.get("message", ""),
                                "from": msg.get("from", {}).get("name", "unknown"),
                                "created_at": msg.get("created_time", "")
                            })
                            self.processed_ids.add(mid)

        except Exception as e:
            self.logger.error(f"Error checking Facebook: {e}")
            self.consecutive_errors += 1

        return items

    def check_instagram(self) -> list:
        """Check Instagram Business Account for new comments and mentions."""
        if not self.ig_token or not self.ig_user_id:
            self.logger.warning("INSTAGRAM_ACCESS_TOKEN or INSTAGRAM_USER_ID not set in .env")
            return []
        
        # Circuit breaker: stop if too many consecutive errors
        if self.consecutive_errors >= MAX_RETRIES:
            self.logger.error(f"Circuit breaker triggered: {self.consecutive_errors} consecutive errors")
            return []

        items = []

        try:
            # Get recent media comments
            media = self._graph_get(
                f"{self.ig_user_id}/media",
                self.ig_token,
                {"fields": "id,caption,timestamp", "limit": 5}
            )

            if "error" in media:
                self.logger.error(f"Instagram API error: {media['error'].get('message', 'Unknown error')}")
                return []

            for post in media.get("data", []):
                comments = self._graph_get(
                    f"{post['id']}/comments",
                    self.ig_token,
                    {"fields": "id,text,username,timestamp"}
                )
                
                if "data" in comments:
                    for comment in comments["data"]:
                        cid = comment.get("id", "")
                        if cid and cid not in self.processed_ids:
                            items.append({
                                "platform": "instagram",
                                "type": "comment",
                                "id": cid,
                                "post_id": post.get("id"),
                                "text": comment.get("text", ""),
                                "from": comment.get("username", "unknown"),
                                "created_at": comment.get("timestamp", "")
                            })
                            self.processed_ids.add(cid)

            # Check mentions
            mentions = self._graph_get(
                f"{self.ig_user_id}/tags",
                self.ig_token,
                {"fields": "id,caption,timestamp,username"}
            )
            
            if "data" in mentions:
                for mention in mentions["data"]:
                    mid = mention.get("id", "")
                    if mid and mid not in self.processed_ids:
                        items.append({
                            "platform": "instagram",
                            "type": "mention",
                            "id": mid,
                            "text": mention.get("caption", ""),
                            "from": mention.get("username", "unknown"),
                            "created_at": mention.get("timestamp", "")
                        })
                        self.processed_ids.add(mid)

        except Exception as e:
            self.logger.error(f"Error checking Instagram: {e}")
            self.consecutive_errors += 1

        return items

    def check_for_updates(self) -> list:
        """Check both platforms for updates."""
        items = []
        if self.platform in ("facebook", "both"):
            items += self.check_facebook()
        if self.platform in ("instagram", "both"):
            items += self.check_instagram()
        self._save_processed()
        return items
    
    def get_status(self) -> dict:
        """Get watcher health status."""
        return {
            "platform": self.platform,
            "facebook_configured": bool(self.fb_token and self.fb_page_id),
            "instagram_configured": bool(self.ig_token and self.ig_user_id),
            "consecutive_errors": self.consecutive_errors,
            "last_success": self.last_success.isoformat() if self.last_success else None,
            "processed_items": len(self.processed_ids),
            "api_calls": self.api_calls,
            "circuit_breaker_active": self.consecutive_errors >= MAX_RETRIES
        }

    def create_action_file(self, item: dict) -> Path:
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        platform = item.get("platform", "social").upper()
        item_type = item.get("type", "post").upper()
        filename = f"{platform}_{item_type}_{item['id'][:12]}_{ts}.md"
        filepath = self.needs_action / filename

        priority = "P2" if item_type == "MESSAGE" else "P3"
        content = f"""---
type: {platform.lower()}_{item['type']}
platform: {platform}
item_id: {item['id']}
from: {item.get('from', 'unknown')}
received: {datetime.now().isoformat()}
priority: {priority}
status: pending
---

# {platform} {item_type.title()} — Action Required

**Platform:** {platform}
**Type:** {item_type}
**From:** {item.get('from', 'unknown')}
**Time:** {item.get('created_at', 'unknown')}

## Content

> {item.get('text', '(no content)')}

## Suggested Actions

1. Review {item_type.lower()} content
2. Draft reply if needed → place in /Pending_Approval
3. If spam/irrelevant → mark as done and move to /Done

## Instructions for Claude

- Check Company_Handbook.md tone guidelines before replying
- All public replies need /Pending_Approval sign-off
- Log action taken in /Logs/{datetime.now().strftime('%Y-%m-%d')}.md
"""
        self.needs_action.mkdir(parents=True, exist_ok=True)
        filepath.write_text(content, encoding="utf-8")
        self.logger.info(f"Created action file: {filename}")
        return filepath

    def run(self):
        self.logger.info(f"Facebook/Instagram Watcher started (platform: {self.platform}, interval: 5 min)")
        while True:
            try:
                items = self.check_for_updates()
                for item in items:
                    self.create_action_file(item)
                if items:
                    self.logger.info(f"Processed {len(items)} social item(s)")
                else:
                    self.logger.debug("No new social activity")
            except Exception as e:
                self.logger.error(f"Watcher error: {e}")
                self._log_error(str(e))
            time.sleep(self.check_interval)

    def _log_error(self, error: str):
        errors_file = self.vault_path / "Logs" / "errors.md"
        errors_file.parent.mkdir(parents=True, exist_ok=True)
        ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with open(errors_file, "a", encoding="utf-8") as f:
            f.write(f"\n- [{ts}] [FacebookWatcher] {error}")


def auth_guide():
    print("""
=== Facebook & Instagram OAuth Setup ===

FACEBOOK:
1. Go to https://developers.facebook.com/
2. Create an App → Business type
3. Add "Pages API" product
4. Generate a Page Access Token (long-lived)
5. Get your Page ID from your Facebook Page settings

INSTAGRAM:
1. Connect Instagram Business Account to your Facebook Page
2. In the same Facebook App, add "Instagram Graph API"
3. Generate Instagram access token with instagram_basic + instagram_manage_comments permissions
4. Get your Instagram User ID

Add to your .env file:
  FACEBOOK_ACCESS_TOKEN=your_page_access_token
  FACEBOOK_PAGE_ID=your_page_id
  INSTAGRAM_ACCESS_TOKEN=your_ig_access_token
  INSTAGRAM_USER_ID=your_ig_user_id

Then run:
  python watchers/facebook_watcher.py --vault ./AI_Employee_Vault --watch
""")


def main():
    parser = argparse.ArgumentParser(description="Facebook/Instagram Watcher for AI Employee")
    parser.add_argument("--vault", default="./AI_Employee_Vault")
    parser.add_argument("--watch", action="store_true")
    parser.add_argument("--auth", action="store_true")
    parser.add_argument("--platform", choices=["facebook", "instagram", "both"], default="both")
    parser.add_argument("--status", action="store_true", help="Show watcher status and exit")
    args = parser.parse_args()

    if args.auth:
        auth_guide()
        return

    if not REQUESTS_AVAILABLE:
        print("ERROR: requests not installed. Run: pip install requests")
        sys.exit(1)

    watcher = FacebookInstagramWatcher(args.vault, platform=args.platform)

    if args.status:
        status = watcher.get_status()
        print("\n=== Facebook/Instagram Watcher Status ===\n")
        print(f"Platform: {status['platform']}")
        print(f"Facebook Configured: {'✅' if status['facebook_configured'] else '❌'}")
        print(f"Instagram Configured: {'✅' if status['instagram_configured'] else '❌'}")
        print(f"Consecutive Errors: {status['consecutive_errors']}")
        print(f"Circuit Breaker Active: {'⚠️ YES' if status['circuit_breaker_active'] else '✅ No'}")
        print(f"Processed Items: {status['processed_items']}")
        print(f"API Calls: {status['api_calls']}")
        if status['last_success']:
            print(f"Last Success: {status['last_success']}")
        else:
            print("Last Success: Never")
        print()
        return

    if args.watch:
        watcher.run()
    else:
        items = watcher.check_for_updates()
        for item in items:
            watcher.create_action_file(item)
        print(f"Processed {len(items)} social item(s)")


if __name__ == "__main__":
    main()
