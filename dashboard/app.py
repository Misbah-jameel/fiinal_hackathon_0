#!/usr/bin/env python3
"""
AI Employee Dashboard - Backend API
Flask server for vault monitoring and approvals
"""

import os
import json
import shutil
from datetime import datetime
from pathlib import Path
from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__, static_folder='.', static_url_path='')
CORS(app)

# Configuration
VAULT_PATH = Path(os.getenv("VAULT_PATH", "./AI_Employee_Vault"))
DRY_RUN = os.getenv("DRY_RUN", "true").lower() == "true"

# Folders to monitor
VAULT_FOLDERS = [
    "Inbox",
    "Needs_Action",
    "In_Progress",
    "Plans",
    "Pending_Approval",
    "Approved",
    "Rejected",
    "Done",
    "Logs",
    "Audit/json",
    "Briefings",
    "Quarantine",
]


def get_vault_status():
    """Get count of files in each vault folder."""
    status = {}
    for folder in VAULT_FOLDERS:
        folder_path = VAULT_PATH / folder
        if folder_path.exists():
            count = len(list(folder_path.glob("*.md")))
            status[folder.replace("/", "_")] = count
        else:
            status[folder.replace("/", "_")] = 0
    return status


def get_pending_approvals():
    """Get list of pending approval files."""
    pending_dir = VAULT_PATH / "Pending_Approval"
    if not pending_dir.exists():
        return []
    
    approvals = []
    for file in pending_dir.glob("*.md"):
        try:
            with open(file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Extract metadata from file
            approvals.append({
                "id": file.stem,
                "filename": file.name,
                "created": datetime.fromtimestamp(file.stat().st_ctime).isoformat(),
                "modified": datetime.fromtimestamp(file.stat().st_mtime).isoformat(),
                "size": file.stat().st_size,
                "preview": content[:200] + "..." if len(content) > 200 else content,
            })
        except Exception as e:
            approvals.append({
                "id": file.stem,
                "filename": file.name,
                "error": str(e),
            })
    
    return sorted(approvals, key=lambda x: x.get("modified", ""), reverse=True)


def get_needs_action_items():
    """Get list of items needing action."""
    na_dir = VAULT_PATH / "Needs_Action"
    if not na_dir.exists():
        return []
    
    items = []
    for file in na_dir.glob("*.md"):
        try:
            with open(file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            items.append({
                "id": file.stem,
                "filename": file.name,
                "created": datetime.fromtimestamp(file.stat().st_ctime).isoformat(),
                "modified": datetime.fromtimestamp(file.stat().st_mtime).isoformat(),
                "preview": content[:200] + "..." if len(content) > 200 else content,
            })
        except Exception as e:
            items.append({
                "id": file.stem,
                "filename": file.name,
                "error": str(e),
            })
    
    return sorted(items, key=lambda x: x.get("modified", ""), reverse=True)


def get_watcher_health():
    """Get watcher health status."""
    health = {
        "gmail": {"status": "unknown", "last_seen": None},
        "linkedin": {"status": "unknown", "last_seen": None},
        "twitter": {"status": "unknown", "last_seen": None},
        "facebook": {"status": "unknown", "last_seen": None},
        "instagram": {"status": "unknown", "last_seen": None},
        "filesystem": {"status": "unknown", "last_seen": None},
    }
    
    # Check PM2 processes
    try:
        import subprocess
        result = subprocess.run(
            ["pm2", "jlist"],
            capture_output=True, text=True, timeout=10
        )
        if result.returncode == 0:
            procs = json.loads(result.stdout)
            watcher_map = {
                "gmail-watcher": "gmail",
                "linkedin-watcher": "linkedin",
                "twitter-watcher": "twitter",
                "facebook-watcher": "facebook",
                "instagram-watcher": "instagram",
                "file-watcher": "filesystem",
            }
            
            for proc in procs:
                name = proc.get("name", "")
                if name in watcher_map:
                    status = proc.get("pm2_env", {}).get("status", "unknown")
                    health[watcher_map[name]] = {
                        "status": "online" if status == "online" else "offline",
                        "last_seen": proc.get("pm2_env", {}).get("restart_time"),
                    }
    except Exception:
        pass
    
    return health


def get_recent_logs(limit=20):
    """Get recent log entries."""
    logs_dir = VAULT_PATH / "Logs"
    if not logs_dir.exists():
        return []
    
    logs = []
    log_files = sorted(logs_dir.glob("*.md"), key=lambda x: x.stat().st_mtime, reverse=True)
    
    for log_file in log_files[:5]:  # Last 5 log files
        try:
            with open(log_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Extract last N lines
            lines = content.strip().split('\n')[-limit:]
            logs.append({
                "file": log_file.name,
                "entries": lines,
            })
        except Exception:
            pass
    
    return logs


def get_dashboard_data():
    """Get main dashboard data."""
    dashboard_file = VAULT_PATH / "Dashboard.md"
    if not dashboard_file.exists():
        return None
    
    try:
        with open(dashboard_file, 'r', encoding='utf-8') as f:
            return f.read()
    except Exception:
        return None


def get_briefings():
    """Get list of CEO briefings."""
    briefings_dir = VAULT_PATH / "Briefings"
    if not briefings_dir.exists():
        return []
    
    briefings = []
    for file in briefings_dir.glob("*.md"):
        briefings.append({
            "id": file.stem,
            "filename": file.name,
            "created": datetime.fromtimestamp(file.stat().st_ctime).isoformat(),
            "size": file.stat().st_size,
        })
    
    return sorted(briefings, key=lambda x: x["created"], reverse=True)


def get_audit_summary():
    """Get audit log summary."""
    audit_dir = VAULT_PATH / "Audit" / "json"
    if not audit_dir.exists():
        return {"total": 0, "today": 0}
    
    today = datetime.now().strftime("%Y-%m-%d")
    total = 0
    today_count = 0
    
    for file in audit_dir.glob("*.jsonl"):
        try:
            with open(file, 'r', encoding='utf-8') as f:
                for line in f:
                    total += 1
                    if today in line:
                        today_count += 1
        except Exception:
            pass
    
    return {"total": total, "today": today_count}


# ==================== API ENDPOINTS ====================

@app.route('/')
def index():
    """Serve dashboard frontend."""
    return send_from_directory(app.static_folder, 'index.html')


@app.route('/api/status')
def api_status():
    """Get overall system status."""
    return jsonify({
        "vault": get_vault_status(),
        "watchers": get_watcher_health(),
        "audit": get_audit_summary(),
        "dry_run": DRY_RUN,
        "timestamp": datetime.now().isoformat(),
    })


@app.route('/api/vault/status')
def api_vault_status():
    """Get vault folder counts."""
    return jsonify(get_vault_status())


@app.route('/api/approvals')
def api_approvals():
    """Get pending approvals."""
    return jsonify(get_pending_approvals())


@app.route('/api/needs-action')
def api_needs_action():
    """Get items needing action."""
    return jsonify(get_needs_action_items())


@app.route('/api/watchers')
def api_watchers():
    """Get watcher health."""
    return jsonify(get_watcher_health())


@app.route('/api/logs')
def api_logs():
    """Get recent logs."""
    limit = request.args.get("limit", 20, type=int)
    return jsonify(get_recent_logs(limit))


@app.route('/api/briefings')
def api_briefings():
    """Get CEO briefings."""
    return jsonify(get_briefings())


@app.route('/api/dashboard')
def api_dashboard():
    """Get dashboard markdown."""
    data = get_dashboard_data()
    return jsonify({"content": data})


@app.route('/api/approve/<file_id>', methods=['POST'])
def api_approve(file_id):
    """Approve a pending action."""
    if DRY_RUN:
        return jsonify({"error": "DRY_RUN mode - no real actions"}), 400
    
    pending_file = VAULT_PATH / "Pending_Approval" / f"{file_id}.md"
    if not pending_file.exists():
        return jsonify({"error": "File not found"}), 404
    
    try:
        # Move to Approved
        approved_dir = VAULT_PATH / "Approved"
        approved_dir.mkdir(parents=True, exist_ok=True)
        
        shutil.move(str(pending_file), str(approved_dir / f"{file_id}.md"))
        
        # Log the action
        log_entry = f"- [{datetime.now().isoformat()}] APPROVED: {file_id}\n"
        log_file = VAULT_PATH / "Logs" / "dashboard.md"
        log_file.parent.mkdir(parents=True, exist_ok=True)
        with open(log_file, 'a', encoding='utf-8') as f:
            f.write(log_entry)
        
        return jsonify({"success": True, "message": f"Approved {file_id}"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/api/reject/<file_id>', methods=['POST'])
def api_reject(file_id):
    """Reject a pending action."""
    if DRY_RUN:
        return jsonify({"error": "DRY_RUN mode - no real actions"}), 400
    
    pending_file = VAULT_PATH / "Pending_Approval" / f"{file_id}.md"
    if not pending_file.exists():
        return jsonify({"error": "File not found"}), 404
    
    try:
        # Move to Rejected
        rejected_dir = VAULT_PATH / "Rejected"
        rejected_dir.mkdir(parents=True, exist_ok=True)
        
        shutil.move(str(pending_file), str(rejected_dir / f"{file_id}.md"))
        
        # Log the action
        log_entry = f"- [{datetime.now().isoformat()}] REJECTED: {file_id}\n"
        log_file = VAULT_PATH / "Logs" / "dashboard.md"
        log_file.parent.mkdir(parents=True, exist_ok=True)
        with open(log_file, 'a', encoding='utf-8') as f:
            f.write(log_entry)
        
        return jsonify({"success": True, "message": f"Rejected {file_id}"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/api/file/<path:file_path>')
def api_get_file(file_path):
    """Get file content."""
    # Security: Only allow vault files
    full_path = VAULT_PATH / file_path
    if not full_path.exists() or not str(full_path).startswith(str(VAULT_PATH)):
        return jsonify({"error": "File not found"}), 404
    
    try:
        with open(full_path, 'r', encoding='utf-8') as f:
            return jsonify({"content": f.read(), "filename": full_path.name})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/api/trigger/<skill>', methods=['POST'])
def api_trigger_skill(skill):
    """Trigger a Claude skill (creates action file)."""
    skills_dir = Path(__file__).parent.parent / "skills"
    skill_file = skills_dir / f"{skill.replace('-', '_')}.py"
    
    if not skill_file.exists():
        return jsonify({"error": f"Skill not found: {skill}"}), 404
    
    # For now, just acknowledge - actual execution would need Claude Code
    return jsonify({
        "success": True,
        "message": f"Skill {skill} triggered (check Claude Code for execution)",
    })


if __name__ == '__main__':
    # Ensure vault exists
    if not VAULT_PATH.exists():
        print("ERROR: Vault not found: {}".format(VAULT_PATH))
        VAULT_PATH.mkdir(parents=True, exist_ok=True)
        print("Created empty vault at: {}".format(VAULT_PATH))
    
    print("\n[AI Employee] Dashboard Backend")
    print("   Vault: {}".format(VAULT_PATH))
    print("   DRY_RUN: {}".format(DRY_RUN))
    print("\n[Web Server] Starting...")
    print("   Local:   http://localhost:5000")
    print("   Network: http://0.0.0.0:5000")
    print("\n   Press Ctrl+C to stop\n")
    
    app.run(host='0.0.0.0', port=5000, debug=True)
