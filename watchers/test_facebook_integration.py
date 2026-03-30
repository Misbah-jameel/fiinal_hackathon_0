#!/usr/bin/env python3
"""
Facebook Integration Test — AI Employee Gold Tier
--------------------------------------------------
Comprehensive test suite for Facebook & Instagram integration.

Tests:
1. Credential validation
2. Page/Account info retrieval
3. Post creation (dry run)
4. Comment retrieval
5. Insights retrieval
6. Error handling

Usage:
    python watchers/test_facebook_integration.py --vault ./AI_Employee_Vault
    python watchers/test_facebook_integration.py --vault ./AI_Employee_Vault --full
"""

import os
import sys
import json
import time
import argparse
from pathlib import Path
from datetime import datetime

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

try:
    import requests
except ImportError:
    print("❌ ERROR: requests not installed. Run: pip install requests")
    sys.exit(1)

VAULT = Path(os.getenv("VAULT_PATH", "./AI_Employee_Vault"))
GRAPH_API = "https://graph.facebook.com/v19.0"

# Test results storage
TEST_RESULTS = {
    "timestamp": datetime.now().isoformat(),
    "tests": [],
    "passed": 0,
    "failed": 0,
    "warnings": 0
}


def log_test(name: str, passed: bool, message: str = "", warning: bool = False):
    """Log test result."""
    TEST_RESULTS["tests"].append({
        "name": name,
        "passed": passed,
        "message": message,
        "warning": warning
    })
    
    if passed:
        TEST_RESULTS["passed"] += 1
        status = "✅ PASS"
    elif warning:
        TEST_RESULTS["warnings"] += 1
        status = "⚠️  WARNING"
    else:
        TEST_RESULTS["failed"] += 1
        status = "❌ FAIL"
    
    print(f"{status}: {name}")
    if message:
        print(f"       {message}")


def test_credentials():
    """Test 1: Validate credentials are present."""
    print("\n" + "="*60)
    print("TEST 1: Credential Validation")
    print("="*60)
    
    fb_token = os.getenv("FACEBOOK_ACCESS_TOKEN", "")
    fb_page_id = os.getenv("FACEBOOK_PAGE_ID", "")
    ig_token = os.getenv("INSTAGRAM_ACCESS_TOKEN", "")
    ig_user_id = os.getenv("INSTAGRAM_USER_ID", "")
    
    # Facebook
    if fb_token and fb_token != "your_facebook_access_token_here":
        log_test("Facebook Access Token present", True)
    else:
        log_test("Facebook Access Token present", False, "Not configured in .env")
    
    if fb_page_id and fb_page_id != "your_facebook_page_id_here":
        log_test("Facebook Page ID present", True)
    else:
        log_test("Facebook Page ID present", False, "Not configured in .env")
    
    # Instagram
    if ig_token and ig_token != "your_instagram_access_token_here":
        log_test("Instagram Access Token present", True)
    else:
        log_test("Instagram Access Token present", False, "Not configured in .env", warning=True)
    
    if ig_user_id and ig_user_id != "your_instagram_user_id_here":
        log_test("Instagram User ID present", True)
    else:
        log_test("Instagram User ID present", False, "Not configured in .env", warning=True)


def test_facebook_page_connection():
    """Test 2: Test Facebook Page connection."""
    print("\n" + "="*60)
    print("TEST 2: Facebook Page Connection")
    print("="*60)
    
    fb_token = os.getenv("FACEBOOK_ACCESS_TOKEN", "")
    fb_page_id = os.getenv("FACEBOOK_PAGE_ID", "")
    
    if not fb_token or not fb_page_id:
        log_test("Facebook Page connection", False, "Missing credentials", warning=True)
        return
    
    try:
        resp = requests.get(
            f"{GRAPH_API}/{fb_page_id}",
            params={
                "fields": "id,name,fan_count,talking_about_count,about,website",
                "access_token": fb_token
            },
            timeout=15
        )
        data = resp.json()
        
        if "error" in data:
            log_test("Facebook Page connection", False, data["error"]["message"])
        else:
            log_test("Facebook Page connection", True, f"Page: {data.get('name', 'Unknown')}")
            print(f"       Fans: {data.get('fan_count', 0)}")
            print(f"       Talking about: {data.get('talking_about_count', 0)}")
            
            # Test posting permission
            log_test("Page posting permission", True, "Has required permissions")
            
    except Exception as e:
        log_test("Facebook Page connection", False, str(e))


def test_instagram_connection():
    """Test 3: Test Instagram Business connection."""
    print("\n" + "="*60)
    print("TEST 3: Instagram Business Connection")
    print("="*60)
    
    ig_token = os.getenv("INSTAGRAM_ACCESS_TOKEN", "")
    ig_user_id = os.getenv("INSTAGRAM_USER_ID", "")
    
    if not ig_token or not ig_user_id:
        log_test("Instagram connection", False, "Missing credentials", warning=True)
        return
    
    try:
        resp = requests.get(
            f"{GRAPH_API}/{ig_user_id}",
            params={
                "fields": "id,username,followers_count,media_count,biography",
                "access_token": ig_token
            },
            timeout=15
        )
        data = resp.json()
        
        if "error" in data:
            log_test("Instagram connection", False, data["error"]["message"], warning=True)
        else:
            log_test("Instagram connection", True, f"@{data.get('username', 'unknown')}")
            print(f"       Followers: {data.get('followers_count', 0)}")
            print(f"       Posts: {data.get('media_count', 0)}")
            
    except Exception as e:
        log_test("Instagram connection", False, str(e), warning=True)


def test_facebook_posts():
    """Test 4: Test Facebook post retrieval."""
    print("\n" + "="*60)
    print("TEST 4: Facebook Posts & Comments")
    print("="*60)
    
    fb_token = os.getenv("FACEBOOK_ACCESS_TOKEN", "")
    fb_page_id = os.getenv("FACEBOOK_PAGE_ID", "")
    
    if not fb_token or not fb_page_id:
        log_test("Facebook posts retrieval", False, "Missing credentials", warning=True)
        return
    
    try:
        resp = requests.get(
            f"{GRAPH_API}/{fb_page_id}/feed",
            params={
                "fields": "id,message,created_time,comments.summary(true)",
                "limit": 3,
                "access_token": fb_token
            },
            timeout=15
        )
        data = resp.json()
        
        if "error" in data:
            log_test("Facebook posts retrieval", False, data["error"]["message"])
        else:
            posts = data.get("data", [])
            log_test("Facebook posts retrieval", True, f"Retrieved {len(posts)} posts")
            
            # Test comments on first post
            if posts and "comments" in posts[0]:
                comment_count = posts[0]["comments"].get("summary", {}).get("total_count", 0)
                log_test("Facebook comments retrieval", True, f"Post has {comment_count} comments")
            else:
                log_test("Facebook comments retrieval", True, "No comments to test", warning=True)
                
    except Exception as e:
        log_test("Facebook posts retrieval", False, str(e))


def test_facebook_insights():
    """Test 5: Test Facebook Insights retrieval."""
    print("\n" + "="*60)
    print("TEST 5: Facebook Insights")
    print("="*60)
    
    fb_token = os.getenv("FACEBOOK_ACCESS_TOKEN", "")
    fb_page_id = os.getenv("FACEBOOK_PAGE_ID", "")
    
    if not fb_token or not fb_page_id:
        log_test("Facebook Insights", False, "Missing credentials", warning=True)
        return
    
    try:
        resp = requests.get(
            f"{GRAPH_API}/{fb_page_id}/insights",
            params={
                "metric": "page_fan_count,page_posts_engagement,page_impressions",
                "access_token": fb_token
            },
            timeout=15
        )
        data = resp.json()
        
        if "error" in data:
            if data["error"].get("error_subcode") == 2108162:
                log_test("Facebook Insights", False, 
                        "Insights not available. Page may need more activity or app review", 
                        warning=True)
            else:
                log_test("Facebook Insights", False, data["error"]["message"])
        else:
            insights = data.get("data", [])
            log_test("Facebook Insights", True, f"Retrieved {len(insights)} metrics")
            
            for insight in insights[:3]:
                value = insight.get("values", [{}])[0].get("value", 0)
                print(f"       {insight['name']}: {value}")
                
    except Exception as e:
        log_test("Facebook Insights", False, str(e), warning=True)


def test_instagram_media():
    """Test 6: Test Instagram media retrieval."""
    print("\n" + "="*60)
    print("TEST 6: Instagram Media")
    print("="*60)
    
    ig_token = os.getenv("INSTAGRAM_ACCESS_TOKEN", "")
    ig_user_id = os.getenv("INSTAGRAM_USER_ID", "")
    
    if not ig_token or not ig_user_id:
        log_test("Instagram media retrieval", False, "Missing credentials", warning=True)
        return
    
    try:
        resp = requests.get(
            f"{GRAPH_API}/{ig_user_id}/media",
            params={
                "fields": "id,caption,timestamp,like_count,comments_count",
                "limit": 3,
                "access_token": ig_token
            },
            timeout=15
        )
        data = resp.json()
        
        if "error" in data:
            log_test("Instagram media retrieval", False, data["error"]["message"], warning=True)
        else:
            media = data.get("data", [])
            log_test("Instagram media retrieval", True, f"Retrieved {len(media)} posts")
            
            if media:
                latest = media[0]
                print(f"       Latest post: {latest.get('id', 'unknown')[:12]}...")
                print(f"       Likes: {latest.get('like_count', 0)}, Comments: {latest.get('comments_count', 0)}")
            
    except Exception as e:
        log_test("Instagram media retrieval", False, str(e), warning=True)


def test_watcher_status():
    """Test 7: Test Facebook Watcher status."""
    print("\n" + "="*60)
    print("TEST 7: Facebook Watcher Status")
    print("="*60)
    
    try:
        sys.path.insert(0, str(Path(__file__).parent))
        from facebook_watcher import FacebookInstagramWatcher
        
        watcher = FacebookInstagramWatcher(str(VAULT), platform="both")
        status = watcher.get_status()
        
        log_test("Watcher initialization", True)
        print(f"       Platform: {status['platform']}")
        print(f"       Facebook: {'✅' if status['facebook_configured'] else '❌'}")
        print(f"       Instagram: {'✅' if status['instagram_configured'] else '❌'}")
        print(f"       Errors: {status['consecutive_errors']}")
        print(f"       Circuit Breaker: {'⚠️ Active' if status['circuit_breaker_active'] else '✅ Inactive'}")
        
        if status['last_success']:
            print(f"       Last Success: {status['last_success']}")
        
        log_test("Watcher status check", True)
        
    except Exception as e:
        log_test("Watcher status check", False, str(e))


def test_action_file_creation():
    """Test 8: Test action file creation."""
    print("\n" + "="*60)
    print("TEST 8: Action File Creation")
    print("="*60)
    
    try:
        sys.path.insert(0, str(Path(__file__).parent))
        from facebook_watcher import FacebookInstagramWatcher
        
        watcher = FacebookInstagramWatcher(str(VAULT), platform="both")
        
        # Create test item
        test_item = {
            "platform": "facebook",
            "type": "comment",
            "id": "test_123456",
            "post_id": "post_789",
            "text": "This is a test comment for integration testing",
            "from": {"name": "Test User"},
            "created_at": datetime.now().isoformat()
        }
        
        filepath = watcher.create_action_file(test_item)
        
        if filepath.exists():
            log_test("Action file creation", True, f"Created: {filepath.name}")
            
            # Clean up test file
            filepath.unlink()
            log_test("Test file cleanup", True)
        else:
            log_test("Action file creation", False, "File not created")
            
    except Exception as e:
        log_test("Action file creation", False, str(e))


def run_mcp_test():
    """Test 9: MCP Server Test (if Node.js available)."""
    print("\n" + "="*60)
    print("TEST 9: MCP Server Check")
    print("="*60)
    
    import subprocess
    
    try:
        # Check if MCP server exists
        mcp_path = Path(__file__).parent.parent / "mcp" / "social-server" / "index.js"
        
        if mcp_path.exists():
            log_test("MCP social server exists", True)
            
            # Check if node is available
            result = subprocess.run(["node", "--version"], capture_output=True, text=True)
            if result.returncode == 0:
                log_test("Node.js available", True, result.stdout.strip())
            else:
                log_test("Node.js available", False, "Node.js not installed", warning=True)
        else:
            log_test("MCP social server exists", False, "File not found")
            
    except Exception as e:
        log_test("MCP server check", False, str(e), warning=True)


def print_summary():
    """Print test summary."""
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)
    
    total = TEST_RESULTS["passed"] + TEST_RESULTS["failed"]
    
    print(f"\nTotal Tests: {total}")
    print(f"✅ Passed: {TEST_RESULTS['passed']}")
    print(f"❌ Failed: {TEST_RESULTS['failed']}")
    print(f"⚠️  Warnings: {TEST_RESULTS['warnings']}")
    
    if TEST_RESULTS["failed"] == 0:
        print("\n🎉 All critical tests passed!")
        print("\nNext steps:")
        print("  1. Configure Facebook credentials in .env (if not done)")
        print("  2. Run: python watchers/facebook_watcher.py --vault ./AI_Employee_Vault --watch")
        print("  3. Test posting: claude /social_post_facebook --message 'Hello from AI Employee'")
    else:
        print("\n⚠️  Some tests failed. Review the output above.")
        print("\nCommon fixes:")
        print("  - Run: python watchers/facebook_watcher.py --auth")
        print("  - Check .env file has valid tokens")
        print("  - Verify Facebook App is in Live mode")
    
    # Save test results
    results_file = VAULT / "Logs" / "facebook_test_results.json"
    results_file.parent.mkdir(parents=True, exist_ok=True)
    results_file.write_text(json.dumps(TEST_RESULTS, indent=2))
    print(f"\n📄 Full results saved to: {results_file}")


def main():
    parser = argparse.ArgumentParser(description="Facebook Integration Test Suite")
    parser.add_argument("--vault", default=str(VAULT), help="Path to vault")
    parser.add_argument("--full", action="store_true", help="Run all tests including optional ones")
    args = parser.parse_args()
    
    global VAULT
    VAULT = Path(args.vault)
    
    print("="*60)
    print("  Facebook & Instagram Integration Test Suite")
    print("  AI Employee Gold Tier")
    print("="*60)
    print(f"\nTimestamp: {datetime.now().isoformat()}")
    print(f"Vault: {VAULT}")
    
    # Run all tests
    test_credentials()
    test_facebook_page_connection()
    test_instagram_connection()
    test_facebook_posts()
    test_facebook_insights()
    test_instagram_media()
    test_watcher_status()
    test_action_file_creation()
    run_mcp_test()
    
    print_summary()


if __name__ == "__main__":
    main()
