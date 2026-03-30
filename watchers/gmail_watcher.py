"""
gmail_watcher.py - Monitors Gmail for unread important emails.

Polls Gmail every 2 minutes (configurable) and creates structured .md action
files in /Needs_Action for each new email detected.

Usage:
    # First-time OAuth setup
    python watchers/gmail_watcher.py --vault ./AI_Employee_Vault --auth

    # Run watcher
    python watchers/gmail_watcher.py --vault ./AI_Employee_Vault

    # Custom interval (seconds)
    python watchers/gmail_watcher.py --vault ./AI_Employee_Vault --interval 60

Requires:
    pip install google-auth google-auth-oauthlib google-api-python-client python-dotenv
"""

import argparse
import json
import logging
import os
import sys
import time
from datetime import datetime
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [GmailWatcher] %(levelname)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("GmailWatcher")

SCOPES = ["https://www.googleapis.com/auth/gmail.readonly"]
GMAIL_QUERY = "is:unread is:important -category:promotions -category:social"

PRIORITY_KEYWORDS = {
    "P1": ["urgent", "asap", "emergency", "critical", "immediately"],
    "P2": ["invoice", "payment", "deadline", "due", "overdue", "contract"],
    "P4": ["newsletter", "unsubscribe", "fyi", "update", "digest"],
}


def get_priority(subject: str, snippet: str) -> str:
    text = (subject + " " + snippet).lower()
    for priority, keywords in PRIORITY_KEYWORDS.items():
        if any(kw in text for kw in keywords):
            return priority
    return "P3"


def authenticate(credentials_path: str, token_path: str):
    """Run OAuth2 flow and save token."""
    try:
        from google.oauth2.credentials import Credentials
        from google_auth_oauthlib.flow import InstalledAppFlow
        from google.auth.transport.requests import Request
    except ImportError:
        logger.error("Missing dependencies. Run: pip install google-auth google-auth-oauthlib google-api-python-client")
        sys.exit(1)

    creds = None
    if Path(token_path).exists():
        creds = Credentials.from_authorized_user_file(token_path, SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(credentials_path, SCOPES)
            creds = flow.run_local_server(port=0)
        Path(token_path).write_text(creds.to_json())
        logger.info(f"Token saved to {token_path}")

    return creds


def build_service(creds):
    from googleapiclient.discovery import build
    return build("gmail", "v1", credentials=creds)


def create_action_file(needs_action_dir: Path, message_id: str, headers: dict, snippet: str) -> Path:
    subject = headers.get("Subject", "No Subject")
    sender = headers.get("From", "Unknown")
    priority = get_priority(subject, snippet)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    safe_id = message_id[-8:]

    filepath = needs_action_dir / f"EMAIL_{safe_id}_{timestamp}.md"

    content = f"""---
type: email
from: {sender}
subject: {subject}
received: {datetime.now().isoformat()}
priority: {priority}
status: pending
gmail_id: {message_id}
---

## Email: {subject}

**From:** {sender}
**Received:** {datetime.now().strftime("%Y-%m-%d %H:%M")}
**Priority:** {priority}

### Snippet
{snippet}

### Suggested Actions
- [ ] Review full email in Gmail
- [ ] Determine required response
- [ ] Draft reply (REQUIRES APPROVAL per Company_Handbook §1)
- [ ] If financial: flag per Company_Handbook §2
- [ ] Update Dashboard.md after processing
"""
    filepath.write_text(content, encoding="utf-8")
    return filepath


def watch(vault_path: Path, credentials_path: str, token_path: str, interval: int, dry_run: bool):
    creds = authenticate(credentials_path, token_path)
    service = build_service(creds)
    needs_action = vault_path / "Needs_Action"
    needs_action.mkdir(parents=True, exist_ok=True)

    processed_ids: set = set()
    logger.info(f"Watching Gmail (query: '{GMAIL_QUERY}', interval: {interval}s)")
    if dry_run:
        logger.info("[DRY RUN] No action files will be written.")

    while True:
        try:
            result = service.users().messages().list(userId="me", q=GMAIL_QUERY).execute()
            messages = result.get("messages", [])
            new_messages = [m for m in messages if m["id"] not in processed_ids]

            if new_messages:
                logger.info(f"Found {len(new_messages)} new message(s).")

            for msg in new_messages:
                full = service.users().messages().get(userId="me", id=msg["id"]).execute()
                headers = {h["name"]: h["value"] for h in full["payload"]["headers"]}
                snippet = full.get("snippet", "")

                processed_ids.add(msg["id"])

                if dry_run:
                    logger.info(f"[DRY RUN] Would create action file for: {headers.get('Subject', '?')}")
                    continue

                path = create_action_file(needs_action, msg["id"], headers, snippet)
                logger.info(f"Created: {path.name}")

        except KeyboardInterrupt:
            logger.info("Watcher stopped.")
            break
        except Exception as e:
            logger.error(f"Error: {e}", exc_info=True)

        time.sleep(interval)


def main():
    parser = argparse.ArgumentParser(description="AI Employee — Gmail Watcher (Silver Tier)")
    parser.add_argument("--vault", default="./AI_Employee_Vault", help="Path to vault")
    parser.add_argument("--auth", action="store_true", help="Run OAuth setup and exit")
    parser.add_argument("--interval", type=int, default=120, help="Poll interval in seconds")
    parser.add_argument("--dry-run", action="store_true", help="Log only, don't write files")
    args = parser.parse_args()

    vault_path = Path(args.vault).resolve()
    credentials_path = os.getenv("GMAIL_CREDENTIALS_PATH", "./credentials.json")
    token_path = os.getenv("GMAIL_TOKEN_PATH", "./token.json")
    dry_run = args.dry_run or os.getenv("DRY_RUN", "true").lower() == "true"

    if not vault_path.exists():
        logger.error(f"Vault not found: {vault_path}")
        sys.exit(1)

    if not Path(credentials_path).exists():
        logger.error(f"credentials.json not found at: {credentials_path}")
        logger.error("Download from Google Cloud Console → APIs → Credentials → OAuth 2.0 Client")
        sys.exit(1)

    if args.auth:
        authenticate(credentials_path, token_path)
        logger.info("Authentication complete. Run without --auth to start watching.")
        return

    watch(vault_path, credentials_path, token_path, args.interval, dry_run)


if __name__ == "__main__":
    main()
