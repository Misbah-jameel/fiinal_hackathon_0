"""
Platinum Tier - Deployment & Configuration Test Script
Run this to verify everything is working
"""

import os
import sys
import subprocess
from pathlib import Path
from datetime import datetime

# Colors
class Colors:
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    NC = '\033[0m'  # No Color

def green(text):
    return f"{Colors.GREEN}{text}{Colors.NC}"

def yellow(text):
    return f"{Colors.YELLOW}{text}{Colors.NC}"

def red(text):
    return f"{Colors.RED}{text}{Colors.NC}"

# Test counters
total = 0
passed = 0
failed = 0

def section(title):
    """Print section header"""
    print("")
    print("-" * 50)
    print(title)
    print("-" * 50)

def test(name, condition, warning=False):
    """Run a test and print result"""
    global total, passed, failed
    total += 1
    
    if condition:
        print(f"✓ {green(name)}")
        passed += 1
        return True
    else:
        if warning:
            print(f"! {yellow(name)}")
        else:
            print(f"✗ {red(name)}")
        failed += 1
        return False

def check_python():
    """Test Python installation"""
    section("1. Python Environment")
    
    try:
        version = sys.version.split()[0]
        test(f"Python installed: {version}", True)
    except:
        test("Python installed", False)
    
    try:
        import dotenv
        test("python-dotenv installed", True)
    except ImportError:
        test("python-dotenv installed", False, warning=True)
    
    try:
        import playwright
        test("playwright installed", True)
    except ImportError:
        test("playwright installed", False, warning=True)

def check_git():
    """Test Git repository"""
    section("2. Git Repository")
    
    vault_git = Path("AI_Employee_Vault/.git")
    test("Git repository initialized", vault_git.exists())
    
    gitignore = Path("AI_Employee_Vault/.gitignore")
    test(".gitignore exists", gitignore.exists())
    
    # Check .gitignore content
    if gitignore.exists():
        content = gitignore.read_text()
        test(".gitignore excludes .env", ".env" in content)
        test(".gitignore excludes secrets", ".secrets" in content or "credentials" in content)

def check_modules():
    """Test Platinum module imports"""
    section("3. Platinum Module Imports")
    
    # Add current directory to path
    sys.path.insert(0, str(Path.cwd()))
    
    modules = [
        ("Cloud Agent config", "platinum.cloud_agent.config"),
        ("Cloud Agent watcher", "platinum.cloud_agent.watcher"),
        ("Cloud Agent drafter", "platinum.cloud_agent.drafter"),
        ("Cloud Agent sync_client", "platinum.cloud_agent.sync_client"),
        ("Local Agent config", "platinum.local_agent.config"),
        ("Local Agent approver", "platinum.local_agent.approver"),
        ("Local Agent executor", "platinum.local_agent.executor"),
        ("Local Agent notifier", "platinum.local_agent.notifier"),
        ("Vault Sync", "platinum.sync.vault_sync"),
        ("Conflict Resolver", "platinum.sync.conflict_resolver"),
        ("Encryption", "platinum.sync.encryption"),
    ]
    
    for name, module in modules:
        try:
            __import__(module)
            test(f"{name} module OK", True)
        except ImportError as e:
            test(f"{name} module OK", False)
            print(f"  Error: {e}")

def check_env():
    """Test environment configuration"""
    section("4. Environment Configuration")
    
    env_file = Path(".env")
    test(".env file exists", env_file.exists())
    
    if env_file.exists():
        content = env_file.read_text()
        test("DRY_RUN mode enabled", "DRY_RUN=true" in content)
        test("GIT_REMOTE_URL configured", "GIT_REMOTE_URL=" in content)
        test("VAULT_PATH configured", "VAULT_PATH=" in content)
        
        # Check for API credentials
        has_gmail = "GMAIL_CLIENT_ID=" in content and len(content.split("GMAIL_CLIENT_ID=")[1].split("\n")[0]) > 10
        has_twitter = "TWITTER_API_KEY=" in content and len(content.split("TWITTER_API_KEY=")[1].split("\n")[0]) > 10
        has_linkedin = "LINKEDIN_CLIENT_ID=" in content and len(content.split("LINKEDIN_CLIENT_ID=")[1].split("\n")[0]) > 10
        
        test("Gmail credentials configured", has_gmail, warning=True)
        test("Twitter credentials configured", has_twitter, warning=True)
        test("LinkedIn credentials configured", has_linkedin)

def check_docker():
    """Test Docker installation"""
    section("5. Docker Environment")
    
    try:
        result = subprocess.run(["docker", "--version"], capture_output=True, text=True)
        if result.returncode == 0:
            test(f"Docker installed: {result.stdout.strip()}", True)
        else:
            test("Docker installed", False, warning=True)
    except FileNotFoundError:
        test("Docker installed (required for Cloud VM)", False, warning=True)
    
    try:
        result = subprocess.run(["docker-compose", "--version"], capture_output=True, text=True)
        if result.returncode == 0:
            test(f"Docker Compose installed: {result.stdout.strip()}", True)
        else:
            test("Docker Compose installed", False, warning=True)
    except FileNotFoundError:
        test("Docker Compose installed (required for Cloud VM)", False, warning=True)

def check_vault_structure():
    """Test vault directory structure"""
    section("6. Vault Structure")
    
    vault_dirs = [
        "AI_Employee_Vault/Needs_Action",
        "AI_Employee_Vault/Plans",
        "AI_Employee_Vault/Pending_Approval",
        "AI_Employee_Vault/Approved",
        "AI_Employee_Vault/Done",
        "AI_Employee_Vault/Logs",
        "AI_Employee_Vault/Audit/json",
        "AI_Employee_Vault/Updates",
        "AI_Employee_Vault/Signals",
        "AI_Employee_Vault/In_Progress/cloud_agent",
        "AI_Employee_Vault/In_Progress/local_agent",
    ]
    
    for dir_path in vault_dirs:
        exists = Path(dir_path).exists()
        test(f"Directory: {dir_path}", exists)

def check_demo():
    """Test demo flow"""
    section("7. Demo Flow")
    
    demo_file = Path("platinum/demo_flow.py")
    test("Demo flow script exists", demo_file.exists())
    
    # Try running demo
    if demo_file.exists():
        try:
            result = subprocess.run(
                [sys.executable, "platinum/demo_flow.py", "--vault", "AI_Employee_Vault", "--speed", "0.5"],
                capture_output=True,
                text=True,
                timeout=30
            )
            test("Demo flow runs successfully", result.returncode == 0)
        except subprocess.TimeoutExpired:
            test("Demo flow completes in time", False, warning=True)
        except Exception as e:
            test("Demo flow runs successfully", False, warning=True)
            print(f"  Error: {e}")

def check_documentation():
    """Test documentation files"""
    section("8. Documentation")
    
    docs = [
        "platinum/README.md",
        "platinum/QUICKSTART.md",
        "platinum/DEPLOYMENT_GUIDE.md",
        "platinum/CREDENTIALS_SETUP.md",
        "platinum/IMPLEMENTATION_SUMMARY.md",
        "README.md",
        "GOLD_TIER_CHECKLIST.md",
    ]
    
    for doc in docs:
        exists = Path(doc).exists()
        test(f"Documentation: {doc}", exists)

def print_summary():
    """Print test summary"""
    print("")
    print("=" * 50)
    print("Test Summary")
    print("=" * 50)
    print(f"Total Tests:  {total}")
    print(f"Passed:       {green(passed)}")
    print(f"Failed:       {red(failed)}")
    
    if total > 0:
        success_rate = (passed * 100) // total
        print(f"Success Rate: {success_rate}%")
    
    print("")
    
    if failed == 0:
        print(green("✓ All tests passed! Platinum Tier ready for deployment."))
        print("")
        print("Next Steps:")
        print("1. Create GitHub/GitLab private repo for vault sync")
        print("2. Configure GIT_REMOTE_URL in .env")
        print("3. Deploy to Cloud VM (see DEPLOYMENT_GUIDE.md)")
        print("4. Configure API credentials (see CREDENTIALS_SETUP.md)")
        return 0
    else:
        print(yellow("! Some tests failed. Please review and fix the issues above."))
        print("")
        print("Recommended Actions:")
        print("1. Fix failed tests marked with ✗")
        print("2. Review warnings marked with !")
        print("3. Configure .env file with your credentials")
        print("4. Set up Git remote for vault sync")
        return 1

def main():
    """Main test runner"""
    print("=" * 50)
    print("AI Employee - Platinum Tier")
    print("Deployment & Configuration Test")
    print("=" * 50)
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Working Directory: {Path.cwd()}")
    
    # Run all tests
    check_python()
    check_git()
    check_modules()
    check_env()
    check_docker()
    check_vault_structure()
    check_demo()
    check_documentation()
    
    # Print summary and exit
    exit_code = print_summary()
    sys.exit(exit_code)

if __name__ == "__main__":
    main()
