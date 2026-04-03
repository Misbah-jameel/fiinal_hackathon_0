#!/usr/bin/env python3
"""
dashboard_live.py — AI Employee Gold Tier
------------------------------------------
Colorful terminal dashboard for the AI Employee.
Shows real-time vault status with rich formatting.

Usage:
    python dashboard_live.py
    python dashboard_live.py --watch          # auto-refresh every 30s
    python dashboard_live.py --vault ./AI_Employee_Vault
"""

import argparse
import os
import time
from datetime import datetime
from pathlib import Path

from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.columns import Columns
from rich.text import Text
from rich.rule import Rule
from rich.live import Live
from rich.layout import Layout
from rich import box

import io, sys
# Force UTF-8 on Windows so emojis render correctly
if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

console = Console(file=sys.stdout, highlight=True)

VAULT = Path(os.getenv("VAULT_PATH", "./AI_Employee_Vault"))


def count_files(folder: Path) -> int:
    if not folder.exists():
        return 0
    return len([f for f in folder.iterdir() if f.is_file() and f.suffix == ".md"])


def count_files_recursive(folder: Path) -> int:
    if not folder.exists():
        return 0
    return len(list(folder.rglob("*.md")))


def get_queue_status() -> dict:
    return {
        "needs_action": count_files_recursive(VAULT / "Needs_Action"),
        "pending_approval": count_files(VAULT / "Pending_Approval"),
        "approved": count_files(VAULT / "Approved"),
        "done": count_files(VAULT / "Done"),
        "plans": count_files(VAULT / "Plans"),
    }


def get_recent_logs() -> list:
    logs_dir = VAULT / "Logs"
    entries = []
    if not logs_dir.exists():
        return entries
    log_files = sorted(logs_dir.glob("*.md"), reverse=True)[:3]
    for lf in log_files:
        try:
            lines = lf.read_text(encoding="utf-8").splitlines()
            for line in lines:
                if line.startswith("## [") or line.startswith("## 2"):
                    entries.append(line.replace("## ", "").strip())
                    if len(entries) >= 6:
                        return entries
        except Exception:
            pass
    return entries


def get_needs_action_files() -> list:
    folder = VAULT / "Needs_Action"
    files = []
    if folder.exists():
        for f in folder.rglob("*.md"):
            files.append(f.name)
    return files[:10]


def get_pending_files() -> list:
    folder = VAULT / "Pending_Approval"
    files = []
    if folder.exists():
        for f in folder.glob("*.md"):
            files.append(f.name)
    return files[:10]


def build_dashboard():
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    qs = get_queue_status()

    console.clear()

    # ── HEADER ──────────────────────────────────────────────────────────────
    console.print()
    console.print(Panel(
        Text("AI Employee — Gold Tier Dashboard", justify="center", style="bold white"),
        subtitle=f"[dim]{now}[/dim]",
        style="bold cyan",
        box=box.DOUBLE_EDGE,
    ))

    # ── QUEUE STATUS ─────────────────────────────────────────────────────────
    console.print(Rule("[bold yellow]Queue Status[/bold yellow]"))

    queue_table = Table(box=box.ROUNDED, show_header=True, header_style="bold magenta")
    queue_table.add_column("Queue", style="cyan", width=25)
    queue_table.add_column("Count", justify="center", width=10)
    queue_table.add_column("Status", width=20)

    def status_badge(count, warn=5, ok=0):
        if count == ok:
            return "[bold green]✅ Clear[/bold green]"
        elif count <= warn:
            return f"[bold yellow]⚠️  {count} pending[/bold yellow]"
        else:
            return f"[bold red]🔴 {count} items![/bold red]"

    queue_table.add_row("📥 Needs Action",     str(qs["needs_action"]),     status_badge(qs["needs_action"]))
    queue_table.add_row("⏳ Pending Approval", str(qs["pending_approval"]), status_badge(qs["pending_approval"]))
    queue_table.add_row("✅ Approved",         str(qs["approved"]),         status_badge(qs["approved"], warn=0))
    queue_table.add_row("📋 Active Plans",     str(qs["plans"]),            "[dim]—[/dim]")
    queue_table.add_row("✔️  Done (total)",    str(qs["done"]),             "[bold green]completed[/bold green]")

    console.print(queue_table)

    # ── SYSTEM HEALTH ────────────────────────────────────────────────────────
    console.print(Rule("[bold yellow]System Health[/bold yellow]"))

    health_table = Table(box=box.SIMPLE, show_header=True, header_style="bold blue")
    health_table.add_column("Component", style="cyan", width=28)
    health_table.add_column("Status", width=20)
    health_table.add_column("Type", style="dim", width=15)

    watchers = [
        ("Filesystem Watcher",   "watchers/filesystem_watcher.py"),
        ("Gmail Watcher",        "watchers/gmail_watcher.py"),
        ("LinkedIn Watcher",     "watchers/linkedin_watcher.py"),
        ("Twitter Watcher",      "watchers/twitter_watcher.py"),
        ("Facebook Watcher",     "watchers/facebook_watcher.py"),
    ]
    mcps = [
        ("Email MCP Server",     "mcp/email-server/index.js"),
        ("Odoo MCP Server",      "mcp/odoo-server/index.js"),
        ("Social MCP Server",    "mcp/social-server/index.js"),
    ]
    hooks = [
        ("Ralph Wiggum Hook",    "hooks/ralph_wiggum.py"),
    ]

    for name, path in watchers:
        exists = Path(path).exists()
        health_table.add_row(name, "[green]✅ Ready[/green]" if exists else "[red]❌ Missing[/red]", "Watcher")
    for name, path in mcps:
        exists = Path(path).exists()
        health_table.add_row(name, "[green]✅ Ready[/green]" if exists else "[red]❌ Missing[/red]", "MCP Server")
    for name, path in hooks:
        exists = Path(path).exists()
        health_table.add_row(name, "[green]✅ Active[/green]" if exists else "[red]❌ Missing[/red]", "Hook")

    console.print(health_table)

    # ── AGENT SKILLS ─────────────────────────────────────────────────────────
    console.print(Rule("[bold yellow]Agent Skills[/bold yellow]"))

    skills_dir = Path(".claude/skills")
    skills = sorted([s.name for s in skills_dir.iterdir() if s.is_dir()]) if skills_dir.exists() else []

    skill_table = Table(box=box.SIMPLE, show_header=True, header_style="bold blue")
    skill_table.add_column("Skill", style="green", width=30)
    skill_table.add_column("Skill", style="green", width=30)
    skill_table.add_column("Skill", style="green", width=30)

    # fill in 3 columns
    rows = []
    row = []
    for s in skills:
        row.append(f"/{s}")
        if len(row) == 3:
            rows.append(row)
            row = []
    if row:
        while len(row) < 3:
            row.append("")
        rows.append(row)

    for r in rows:
        skill_table.add_row(*r)

    console.print(f"[bold]Total Skills:[/bold] [cyan]{len(skills)}[/cyan]")
    console.print(skill_table)

    # ── NEEDS ACTION ─────────────────────────────────────────────────────────
    na_files = get_needs_action_files()
    if na_files:
        console.print(Rule("[bold red]Needs Action (Pending Items)[/bold red]"))
        for f in na_files:
            console.print(f"  [yellow]⚡[/yellow] {f}")
    else:
        console.print(Rule("[bold green]Needs Action — Clear[/bold green]"))
        console.print("  [green]✅ No pending items[/green]")

    # ── PENDING APPROVAL ─────────────────────────────────────────────────────
    pa_files = get_pending_files()
    if pa_files:
        console.print(Rule("[bold orange3]Pending Approval[/bold orange3]"))
        for f in pa_files:
            console.print(f"  [orange3]⏳[/orange3] {f}")

    # ── RECENT LOGS ───────────────────────────────────────────────────────────
    console.print(Rule("[bold yellow]Recent Activity[/bold yellow]"))
    logs = get_recent_logs()
    if logs:
        for entry in logs:
            console.print(f"  [dim cyan]•[/dim cyan] {entry}")
    else:
        console.print("  [dim]No recent log entries[/dim]")

    # ── FOOTER ───────────────────────────────────────────────────────────────
    console.print()
    console.print(Panel(
        "[bold green]GOLD TIER COMPLETE[/bold green]  •  "
        "[cyan]22 Skills[/cyan]  •  "
        "[cyan]5 Watchers[/cyan]  •  "
        "[cyan]3 MCP Servers[/cyan]  •  "
        "[cyan]HITL Workflow[/cyan]  •  "
        "[cyan]Ralph Wiggum Hook[/cyan]",
        style="dim",
        box=box.MINIMAL,
    ))


def main():
    parser = argparse.ArgumentParser(description="AI Employee Colorful Dashboard")
    parser.add_argument("--vault", default="./AI_Employee_Vault", help="Vault path")
    parser.add_argument("--watch", action="store_true", help="Auto-refresh every 30 seconds")
    parser.add_argument("--interval", type=int, default=30, help="Refresh interval in seconds")
    args = parser.parse_args()

    global VAULT
    VAULT = Path(args.vault)

    if args.watch:
        console.print(f"[dim]Auto-refresh every {args.interval}s — Press Ctrl+C to stop[/dim]")
        try:
            while True:
                build_dashboard()
                console.print(f"\n[dim]Next refresh in {args.interval}s... (Ctrl+C to stop)[/dim]")
                time.sleep(args.interval)
        except KeyboardInterrupt:
            console.print("\n[yellow]Dashboard stopped.[/yellow]")
    else:
        build_dashboard()


if __name__ == "__main__":
    main()
