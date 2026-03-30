#!/usr/bin/env python3
"""
Twitter/X Watcher — AI Employee Gold Tier
------------------------------------------
Monitors Twitter/X for:
- Mentions (@username)
- DMs (Direct Messages)
- Important notifications

Creates action files in /Needs_Action for Claude to process.

Usage:
  python watchers/twitter_watcher.py --vault ./AI_Employee_Vault
  python watchers/twitter_watcher.py --vault ./AI_Employee_Vault --watch
  python watchers/twitter_watcher.py --vault ./AI_Employee_Vault --auth
"""

import os
import sys
import json
import time
import argparse
import logging
from pathlib import Path
from datetime import datetime, timezone

# Load .env
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

# Try tweepy (Twitter API v2)
try:
    import tweepy
    TWEEPY_AVAILABLE = True
except ImportError:
    TWEEPY_AVAILABLE = False

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


class TwitterWatcher(BaseWatcher):
    def __init__(self, vault_path: str):
        super().__init__(vault_path, check_interval=300)  # 5 min

        self.api_key = os.getenv("TWITTER_CONSUMER_KEY", "")
        self.api_secret = os.getenv("TWITTER_CONSUMER_SECRET", "")
        self.access_token = os.getenv("TWITTER_ACCESS_TOKEN", "")
        self.access_secret = os.getenv("TWITTER_ACCESS_TOKEN_SECRET", "")
        self.bearer_token = os.getenv("TWITTER_BEARER_TOKEN", "")

        self.processed_ids_file = self.vault_path / "Logs" / "twitter_processed.json"
        self.processed_ids = self._load_processed()

        self.client = None
        self.me = None

        if TWEEPY_AVAILABLE and self.bearer_token:
            self._init_client()

    def _load_processed(self) -> set:
        if self.processed_ids_file.exists():
            try:
                data = json.loads(self.processed_ids_file.read_text())
                return set(data)
            except Exception:
                pass
        return set()

    def _save_processed(self):
        self.processed_ids_file.parent.mkdir(parents=True, exist_ok=True)
        self.processed_ids_file.write_text(
            json.dumps(list(self.processed_ids)[-500:])  # keep last 500
        )

    def _init_client(self):
        try:
            self.client = tweepy.Client(
                bearer_token=self.bearer_token,
                consumer_key=self.api_key,
                consumer_secret=self.api_secret,
                access_token=self.access_token,
                access_token_secret=self.access_secret,
                wait_on_rate_limit=True
            )
            me = self.client.get_me()
            if me.data:
                self.me = me.data
                self.logger.info(f"Twitter authenticated as @{self.me.username}")
        except Exception as e:
            self.logger.error(f"Twitter auth failed: {e}")
            self.client = None

    def check_for_updates(self) -> list:
        if not self.client or not self.me:
            self.logger.warning("Twitter client not initialized — check credentials in .env")
            return []

        items = []

        # Check mentions
        try:
            mentions = self.client.get_users_mentions(
                id=self.me.id,
                max_results=10,
                tweet_fields=["created_at", "author_id", "text"]
            )
            if mentions.data:
                for tweet in mentions.data:
                    if str(tweet.id) not in self.processed_ids:
                        items.append({
                            "type": "mention",
                            "id": str(tweet.id),
                            "text": tweet.text,
                            "author_id": str(tweet.author_id),
                            "created_at": str(tweet.created_at)
                        })
                        self.processed_ids.add(str(tweet.id))
        except Exception as e:
            self.logger.error(f"Error fetching mentions: {e}")

        # Check DMs
        try:
            dms = self.client.get_direct_message_events(max_results=5)
            if dms.data:
                for dm in dms.data:
                    if str(dm.id) not in self.processed_ids:
                        items.append({
                            "type": "dm",
                            "id": str(dm.id),
                            "text": dm.text if hasattr(dm, "text") else "(no text)",
                            "sender_id": str(dm.sender_id) if hasattr(dm, "sender_id") else "unknown",
                            "created_at": str(getattr(dm, "created_at", datetime.now()))
                        })
                        self.processed_ids.add(str(dm.id))
        except Exception as e:
            self.logger.debug(f"DMs not available (requires Elevated access): {e}")

        self._save_processed()
        return items

    def create_action_file(self, item: dict) -> Path:
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        item_type = item.get("type", "tweet").upper()
        filename = f"TWITTER_{item_type}_{item['id']}_{ts}.md"
        filepath = self.needs_action / filename

        priority = "P2" if item_type == "DM" else "P3"
        content = f"""---
type: twitter_{item['type']}
tweet_id: {item['id']}
from: {item.get('author_id', item.get('sender_id', 'unknown'))}
received: {datetime.now().isoformat()}
priority: {priority}
status: pending
---

# Twitter {item_type.title()} — Action Required

**Type:** {item_type}
**ID:** {item['id']}
**From:** @{item.get('author_id', item.get('sender_id', 'unknown'))}
**Time:** {item.get('created_at', 'unknown')}

## Content

> {item.get('text', '(no content)')}

## Suggested Actions

1. Review tweet/DM content
2. Draft reply if needed → place in /Pending_Approval
3. If spam/irrelevant → mark as done

## Instructions for Claude

- Check Company_Handbook.md tone guidelines before replying
- All replies need /Pending_Approval sign-off
- Log action taken in /Logs/{datetime.now().strftime('%Y-%m-%d')}.md
"""
        self.needs_action.mkdir(parents=True, exist_ok=True)
        filepath.write_text(content, encoding="utf-8")
        self.logger.info(f"Created action file: {filename}")
        return filepath

    def run(self):
        self.logger.info("Twitter Watcher started (interval: 5 min)")
        while True:
            try:
                items = self.check_for_updates()
                for item in items:
                    self.create_action_file(item)
                if items:
                    self.logger.info(f"Processed {len(items)} Twitter item(s)")
                else:
                    self.logger.debug("No new Twitter activity")
            except Exception as e:
                self.logger.error(f"Watcher loop error: {e}")
                self._log_error(str(e))
            time.sleep(self.check_interval)

    def _log_error(self, error: str):
        errors_file = self.vault_path / "Logs" / "errors.md"
        errors_file.parent.mkdir(parents=True, exist_ok=True)
        ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with open(errors_file, "a", encoding="utf-8") as f:
            f.write(f"\n- [{ts}] [TwitterWatcher] {error}")


def auth_flow():
    """Interactive OAuth flow for Twitter credentials."""
    print("\n=== Twitter/X OAuth Setup ===")
    print("1. Go to https://developer.twitter.com/en/portal/projects-and-apps")
    print("2. Create a new App with Read + Write permissions")
    print("3. Generate Access Token and Secret\n")

    api_key = input("API Key (Consumer Key): ").strip()
    api_secret = input("API Secret (Consumer Secret): ").strip()
    bearer_token = input("Bearer Token: ").strip()
    access_token = input("Access Token: ").strip()
    access_secret = input("Access Token Secret: ").strip()

    env_path = Path(".env")
    existing = env_path.read_text() if env_path.exists() else ""

    # Remove old twitter entries
    lines = [l for l in existing.splitlines()
             if not l.startswith("TWITTER_")]

    lines += [
        f"TWITTER_API_KEY={api_key}",
        f"TWITTER_API_SECRET={api_secret}",
        f"TWITTER_BEARER_TOKEN={bearer_token}",
        f"TWITTER_ACCESS_TOKEN={access_token}",
        f"TWITTER_ACCESS_SECRET={access_secret}",
    ]

    env_path.write_text("\n".join(lines) + "\n")
    print("\n✅ Twitter credentials saved to .env")
    print("Run without --auth to start watching.")


def main():
    parser = argparse.ArgumentParser(description="Twitter/X Watcher for AI Employee")
    parser.add_argument("--vault", default="./AI_Employee_Vault", help="Vault path")
    parser.add_argument("--watch", action="store_true", help="Run continuously")
    parser.add_argument("--auth", action="store_true", help="Run auth setup")
    parser.add_argument("--once", action="store_true", help="Run once and exit")
    args = parser.parse_args()

    if args.auth:
        auth_flow()
        return

    if not TWEEPY_AVAILABLE:
        print("ERROR: tweepy not installed. Run: pip install tweepy")
        sys.exit(1)

    watcher = TwitterWatcher(args.vault)

    if args.watch:
        watcher.run()
    else:
        # Single check
        items = watcher.check_for_updates()
        for item in items:
            watcher.create_action_file(item)
        print(f"Processed {len(items)} Twitter item(s)")


if __name__ == "__main__":
    main()
