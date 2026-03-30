"""
linkedin_watcher.py - LinkedIn posting and notification watcher.

Two modes:
  --watch : Monitor LinkedIn notifications (Playwright-based) for engagement
  --post  : Post an approved LinkedIn post file via LinkedIn API
  --auth  : Run OAuth flow and save access token

Usage:
    python watchers/linkedin_watcher.py --vault ./AI_Employee_Vault --auth
    python watchers/linkedin_watcher.py --vault ./AI_Employee_Vault --watch
    python watchers/linkedin_watcher.py --post ./AI_Employee_Vault/Approved/LINKEDIN_win_2026-02-26.md

Requires:
    pip install requests python-dotenv playwright
    playwright install chromium
"""

import argparse
import json
import logging
import os
import re
import sys
import time
from datetime import datetime
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [LinkedInWatcher] %(levelname)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("LinkedInWatcher")

DRY_RUN = os.getenv("DRY_RUN", "true").lower() == "true"

LINKEDIN_API_BASE = "https://api.linkedin.com/v2"
ACCESS_TOKEN = os.getenv("LINKEDIN_ACCESS_TOKEN", "")
PERSON_URN = os.getenv("LINKEDIN_PERSON_URN", "")

TRIGGER_KEYWORDS = ["pricing", "invoice", "help", "interested", "service", "quote", "urgent"]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _headers():
    return {
        "Authorization": f"Bearer {ACCESS_TOKEN}",
        "Content-Type": "application/json",
        "X-Restli-Protocol-Version": "2.0.0",
    }


def _log_action(vault_path: Path, action: str, detail: str, result: str):
    log_dir = vault_path / "Logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    log_file = log_dir / f"{datetime.now().strftime('%Y-%m-%d')}.md"
    entry = (
        f"\n## {datetime.now().strftime('%H:%M:%S')} — linkedin_{action}\n\n"
        f"- **Detail:** {detail}\n"
        f"- **Result:** {result}\n"
        f"- **Dry Run:** {DRY_RUN}\n"
    )
    with open(log_file, "a", encoding="utf-8") as f:
        f.write(entry)


# ---------------------------------------------------------------------------
# Post an approved LinkedIn file
# ---------------------------------------------------------------------------

def _extract_post_content(md_path: Path) -> str:
    """Extract the post body from a LINKEDIN_*.md approval file."""
    text = md_path.read_text(encoding="utf-8")
    # Content lives between the two "---" horizontal rules in the body
    match = re.search(r"---\n\n(.+?)\n\n---", text, re.DOTALL)
    if match:
        return match.group(1).strip()
    # Fallback: everything after frontmatter
    parts = text.split("---", 2)
    return parts[2].strip() if len(parts) >= 3 else text.strip()


def post_linkedin(md_path: Path, vault_path: Path):
    """Post an approved LinkedIn .md file."""
    if not md_path.exists():
        logger.error(f"File not found: {md_path}")
        sys.exit(1)

    content = _extract_post_content(md_path)
    logger.info(f"Posting to LinkedIn ({len(content)} chars)...")

    if DRY_RUN:
        logger.info("[DRY RUN] Would post:\n" + content[:200] + "...")
        _log_action(vault_path, "post", md_path.name, "dry_run")
        return

    if not ACCESS_TOKEN or not PERSON_URN:
        logger.error("LINKEDIN_ACCESS_TOKEN and LINKEDIN_PERSON_URN must be set in .env")
        sys.exit(1)

    import requests

    payload = {
        "author": PERSON_URN,
        "lifecycleState": "PUBLISHED",
        "specificContent": {
            "com.linkedin.ugc.ShareContent": {
                "shareCommentary": {"text": content},
                "shareMediaCategory": "NONE",
            }
        },
        "visibility": {
            "com.linkedin.ugc.MemberNetworkVisibility": "PUBLIC"
        },
    }

    resp = requests.post(
        f"{LINKEDIN_API_BASE}/ugcPosts",
        headers=_headers(),
        json=payload,
        timeout=30,
    )

    if resp.status_code in (200, 201):
        post_id = resp.headers.get("x-restli-id", "unknown")
        logger.info(f"Posted successfully. Post ID: {post_id}")
        _log_action(vault_path, "post", md_path.name, f"success — post_id={post_id}")

        # Move to Done
        done_dir = vault_path / "Done"
        done_dir.mkdir(exist_ok=True)
        md_path.rename(done_dir / md_path.name)
        logger.info(f"Moved to /Done/")
    else:
        logger.error(f"LinkedIn API error {resp.status_code}: {resp.text}")
        _log_action(vault_path, "post", md_path.name, f"error — {resp.status_code}")


# ---------------------------------------------------------------------------
# Watch LinkedIn notifications (Playwright)
# ---------------------------------------------------------------------------

def watch_notifications(vault_path: Path, session_path: Path, interval: int):
    """Monitor LinkedIn for engagement opportunities using Playwright."""
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        logger.error("Playwright not installed. Run: pip install playwright && playwright install chromium")
        sys.exit(1)

    needs_action = vault_path / "Needs_Action"
    needs_action.mkdir(parents=True, exist_ok=True)
    processed: set = set()

    logger.info(f"Watching LinkedIn notifications (interval: {interval}s)")

    while True:
        try:
            with sync_playwright() as p:
                browser = p.chromium.launch_persistent_context(
                    str(session_path), headless=True
                )
                page = browser.pages[0] if browser.pages else browser.new_page()
                page.goto("https://www.linkedin.com/notifications/")
                page.wait_for_timeout(3000)

                items = page.query_selector_all("[data-urn]")
                new_items = []
                for item in items:
                    urn = item.get_attribute("data-urn") or ""
                    text = (item.inner_text() or "").lower()
                    if urn not in processed and any(kw in text for kw in TRIGGER_KEYWORDS):
                        new_items.append({"urn": urn, "text": text})
                        processed.add(urn)

                browser.close()

                for item in new_items:
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    filepath = needs_action / f"LINKEDIN_notification_{timestamp}.md"
                    content = f"""---
type: linkedin
source: notification
urn: {item['urn']}
received: {datetime.now().isoformat()}
priority: P2
status: pending
---

## LinkedIn Notification Detected

**Trigger keywords found in:** notification feed

### Content Snippet
{item['text'][:500]}

### Suggested Actions
- [ ] Review notification in LinkedIn
- [ ] Draft a reply (REQUIRES APPROVAL per Company_Handbook §1)
- [ ] Consider creating a LinkedIn post about this topic
- [ ] Update Dashboard.md
"""
                    filepath.write_text(content, encoding="utf-8")
                    logger.info(f"Created action file: {filepath.name}")
                    _log_action(vault_path, "notification", filepath.name, "action_file_created")

        except KeyboardInterrupt:
            logger.info("LinkedIn watcher stopped.")
            break
        except Exception as e:
            logger.error(f"Error: {e}", exc_info=True)

        time.sleep(interval)


# ---------------------------------------------------------------------------
# OAuth helper
# ---------------------------------------------------------------------------

def run_auth():
    """Print OAuth URL and instructions."""
    client_id = os.getenv("LINKEDIN_CLIENT_ID", "YOUR_CLIENT_ID")
    redirect_uri = "http://localhost:8080/callback"
    scope = "r_liteprofile%20w_member_social"

    auth_url = (
        f"https://www.linkedin.com/oauth/v2/authorization"
        f"?response_type=code&client_id={client_id}"
        f"&redirect_uri={redirect_uri}&scope={scope}"
    )

    print("\n=== LinkedIn OAuth Setup ===")
    print(f"1. Open this URL in your browser:\n   {auth_url}")
    print("2. Log in and authorize the app")
    print("3. Copy the 'code' parameter from the redirect URL")
    print("4. Exchange it for an access token:")
    print(f"""
    curl -X POST https://www.linkedin.com/oauth/v2/accessToken \\
      -d "grant_type=authorization_code" \\
      -d "code=YOUR_CODE" \\
      -d "redirect_uri={redirect_uri}" \\
      -d "client_id={client_id}" \\
      -d "client_secret=YOUR_CLIENT_SECRET"
    """)
    print("5. Add the access_token to your .env as LINKEDIN_ACCESS_TOKEN")
    print("6. Add your profile URN as LINKEDIN_PERSON_URN (e.g. urn:li:person:ABC123)")


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="AI Employee — LinkedIn Watcher (Silver Tier)")
    parser.add_argument("--vault", default="./AI_Employee_Vault", help="Path to vault")
    parser.add_argument("--auth", action="store_true", help="Print OAuth setup instructions")
    parser.add_argument("--watch", action="store_true", help="Watch LinkedIn notifications")
    parser.add_argument("--post", type=str, help="Path to approved LINKEDIN_*.md file to post")
    parser.add_argument("--interval", type=int, default=300, help="Notification check interval (seconds)")
    parser.add_argument("--session", default="./linkedin_session", help="Playwright session directory")
    args = parser.parse_args()

    vault_path = Path(args.vault).resolve()

    if args.auth:
        run_auth()
        return

    if args.post:
        post_linkedin(Path(args.post), vault_path)
        return

    if args.watch:
        session_path = Path(args.session).resolve()
        watch_notifications(vault_path, session_path, args.interval)
        return

    parser.print_help()


if __name__ == "__main__":
    main()
