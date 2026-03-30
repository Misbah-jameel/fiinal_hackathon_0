#!/usr/bin/env python3
"""
twitter_poster.py - Twitter/X posting for AI Employee Gold Tier
----------------------------------------------------------------
Posts approved tweets to Twitter/X using Twitter API v2.

Usage:
    python watchers/twitter_poster.py --vault ./AI_Employee_Vault --post ./AI_Employee_Vault/Approved/TWITTER_tweet_2026-03-26.md
    python watchers/twitter_poster.py --auth  # Run auth setup

Requires:
    pip install tweepy python-dotenv
"""

import argparse
import json
import logging
import os
import re
import sys
from datetime import datetime
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [TwitterPoster] %(levelname)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("TwitterPoster")

DRY_RUN = os.getenv("DRY_RUN", "true").lower() == "true"

# Twitter credentials
CONSUMER_KEY = os.getenv("TWITTER_CONSUMER_KEY", "")
CONSUMER_SECRET = os.getenv("TWITTER_CONSUMER_SECRET", "")
ACCESS_TOKEN = os.getenv("TWITTER_ACCESS_TOKEN", "")
ACCESS_TOKEN_SECRET = os.getenv("TWITTER_ACCESS_TOKEN_SECRET", "")
BEARER_TOKEN = os.getenv("TWITTER_BEARER_TOKEN", "")

try:
    import tweepy
    TWEEPY_AVAILABLE = True
except ImportError:
    TWEEPY_AVAILABLE = False


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _log_action(vault_path: Path, action: str, detail: str, result: str):
    log_dir = vault_path / "Logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    log_file = log_dir / f"{datetime.now().strftime('%Y-%m-%d')}.md"
    entry = (
        f"\n## {datetime.now().strftime('%H:%M:%S')} — twitter_{action}\n\n"
        f"- **Detail:** {detail}\n"
        f"- **Result:** {result}\n"
        f"- **Dry Run:** {DRY_RUN}\n"
    )
    with open(log_file, "a", encoding="utf-8") as f:
        f.write(entry)


def _get_client():
    """Initialize Twitter API client."""
    if not TWEEPY_AVAILABLE:
        logger.error("tweepy not installed. Run: pip install tweepy")
        return None
    
    if not all([CONSUMER_KEY, CONSUMER_SECRET, ACCESS_TOKEN, ACCESS_TOKEN_SECRET]):
        logger.error("Twitter credentials not set in .env")
        return None
    
    try:
        client = tweepy.Client(
            consumer_key=CONSUMER_KEY,
            consumer_secret=CONSUMER_SECRET,
            access_token=ACCESS_TOKEN,
            access_token_secret=ACCESS_TOKEN_SECRET,
            wait_on_rate_limit=True
        )
        # Test authentication
        me = client.get_me()
        if me.data:
            logger.info(f"Authenticated as @{me.data.username}")
        return client
    except Exception as e:
        logger.error(f"Twitter auth failed: {e}")
        return None


# ---------------------------------------------------------------------------
# Extract tweet content from approved file
# ---------------------------------------------------------------------------

def _extract_tweet_content(md_path: Path) -> str:
    """Extract the tweet text from a TWITTER_*.md approval file."""
    if not md_path.exists():
        raise FileNotFoundError(f"File not found: {md_path}")
    
    text = md_path.read_text(encoding="utf-8")
    
    # Look for content between horizontal rules or after frontmatter
    match = re.search(r"---\n\n(.+?)\n\n---", text, re.DOTALL)
    if match:
        return match.group(1).strip()
    
    # Fallback: everything after frontmatter
    parts = text.split("---", 2)
    if len(parts) >= 3:
        return parts[2].strip()
    
    # Last resort: return whole content
    return text.strip()


# ---------------------------------------------------------------------------
# Post to Twitter
# ---------------------------------------------------------------------------

def post_tweet(md_path: Path, vault_path: Path):
    """Post an approved tweet from a .md file."""
    logger.info(f"Processing: {md_path.name}")
    
    try:
        content = _extract_tweet_content(md_path)
    except FileNotFoundError as e:
        logger.error(str(e))
        sys.exit(1)
    
    # Check tweet length (Twitter limit is 280 chars)
    if len(content) > 280:
        logger.warning(f"Tweet is {len(content)} chars (max 280). Truncating...")
        content = content[:277] + "..."
    
    logger.info(f"Tweet content ({len(content)} chars):\n{content[:100]}...")
    
    if DRY_RUN:
        logger.info("[DRY RUN] Would post to Twitter")
        _log_action(vault_path, "post", md_path.name, "dry_run")
        return
    
    client = _get_client()
    if not client:
        logger.error("Cannot post - authentication failed")
        sys.exit(1)
    
    try:
        response = client.create_tweet(text=content)
        
        if response.data:
            tweet_id = response.data["id"]
            tweet_url = f"https://twitter.com/i/web/status/{tweet_id}"
            logger.info(f"Posted successfully! {tweet_url}")
            _log_action(vault_path, "post", md_path.name, f"success — {tweet_url}")
            
            # Move to Done
            done_dir = vault_path / "Done"
            done_dir.mkdir(exist_ok=True)
            md_path.rename(done_dir / md_path.name)
            logger.info(f"Moved to /Done/")
        else:
            logger.error("Post failed - no response data")
            _log_action(vault_path, "post", md_path.name, "error — no response")
            
    except Exception as e:
        logger.error(f"Twitter API error: {e}")
        _log_action(vault_path, "post", md_path.name, f"error — {str(e)}")


# ---------------------------------------------------------------------------
# OAuth setup helper
# ---------------------------------------------------------------------------

def run_auth():
    """Print OAuth setup instructions."""
    print("\n=== Twitter/X OAuth Setup ===")
    print("Your credentials are already in .env file:")
    print(f"  Consumer Key: {CONSUMER_KEY[:10]}...")
    print(f"  Access Token: {ACCESS_TOKEN[:10]}...")
    print("\nTo get new credentials:")
    print("1. Go to https://developer.twitter.com/en/portal/dashboard")
    print("2. Select your project/app")
    print("3. Go to 'Keys and Tokens'")
    print("4. Generate/regenerate keys as needed")
    print("5. Update .env file with new values")


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="AI Employee — Twitter Poster (Gold Tier)")
    parser.add_argument("--vault", default="./AI_Employee_Vault", help="Path to vault")
    parser.add_argument("--post", type=str, help="Path to approved TWITTER_*.md file to post")
    parser.add_argument("--auth", action="store_true", help="Show auth info")
    parser.add_argument("--test", action="store_true", help="Test Twitter connection")
    args = parser.parse_args()
    
    vault_path = Path(args.vault).resolve()
    
    if args.auth:
        run_auth()
        return
    
    if args.test:
        if not TWEEPY_AVAILABLE:
            print("ERROR: tweepy not installed. Run: pip install tweepy")
            return
        client = _get_client()
        if client:
            print("✓ Twitter connection successful!")
        else:
            print("✗ Twitter connection failed - check .env credentials")
        return
    
    if args.post:
        post_tweet(Path(args.post), vault_path)
        return
    
    parser.print_help()


if __name__ == "__main__":
    main()
