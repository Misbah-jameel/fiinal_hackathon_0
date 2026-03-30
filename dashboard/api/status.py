from http.server import HTTPServer, SimpleHTTPRequestHandler
import json
import os
from datetime import datetime
from pathlib import Path

# Vercel serverless function
def handler(request):
    from http import HTTPStatus
    
    # CORS headers
    headers = {
        'Content-Type': 'application/json',
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Methods': 'GET, POST, OPTIONS',
        'Access-Control-Allow-Headers': 'Content-Type',
    }
    
    # Handle CORS preflight
    if request.method == 'OPTIONS':
        return (200, headers, b'')
    
    # Mock data for demo
    data = {
        "vault": {
            "Needs_Action": 13,
            "Pending_Approval": 0,
            "Approved": 8,
            "Done": 14,
            "In_Progress": 0,
            "Plans": 19,
            "Inbox": 0,
            "Logs": 6,
            "Briefings": 1,
            "Audit_json": 0,
            "Quarantine": 0,
            "Rejected": 0
        },
        "watchers": {
            "gmail": {"status": "unknown", "last_seen": None},
            "linkedin": {"status": "unknown", "last_seen": None},
            "twitter": {"status": "unknown", "last_seen": None},
            "facebook": {"status": "unknown", "last_seen": None},
            "instagram": {"status": "unknown", "last_seen": None},
            "filesystem": {"status": "unknown", "last_seen": None},
        },
        "audit": {"today": 0, "total": 8},
        "dry_run": True,
        "timestamp": datetime.now().isoformat(),
    }
    
    return (200, headers, json.dumps(data).encode())
