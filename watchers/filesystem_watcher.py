"""
filesystem_watcher.py - Monitors the vault /Inbox folder for new files.

When a new file is dropped into /Inbox, this watcher:
  1. Copies it to /Needs_Action/
  2. Creates a companion .md action file describing the file and suggested actions.

Usage:
    python watchers/filesystem_watcher.py --vault <path_to_vault>

Example:
    python watchers/filesystem_watcher.py --vault ./AI_Employee_Vault

Requires:
    pip install watchdog
"""

import argparse
import logging
import shutil
import sys
from datetime import datetime
from pathlib import Path

from watchdog.events import FileSystemEventHandler
from watchdog.observers import Observer

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [FileSystemWatcher] %(levelname)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("FileSystemWatcher")


class InboxEventHandler(FileSystemEventHandler):
    """Handles new files dropped into the /Inbox folder."""

    def __init__(self, vault_path: Path):
        self.inbox = vault_path / "Inbox"
        self.needs_action = vault_path / "Needs_Action"
        self.needs_action.mkdir(parents=True, exist_ok=True)
        self._processed: set[str] = set()

    def on_created(self, event):
        if event.is_directory:
            return

        source = Path(event.src_path)

        # Skip hidden files and already-processed files
        if source.name.startswith(".") or source.suffix == ".md":
            return
        if str(source) in self._processed:
            return

        self._processed.add(str(source))
        logger.info(f"New file detected: {source.name}")
        self._handle_new_file(source)

    def _handle_new_file(self, source: Path):
        """Copy the file and create an action .md file in /Needs_Action."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_name = source.stem.replace(" ", "_")

        # Copy original file to Needs_Action
        dest_file = self.needs_action / f"FILE_{safe_name}_{timestamp}{source.suffix}"
        try:
            shutil.copy2(source, dest_file)
            logger.info(f"Copied to Needs_Action: {dest_file.name}")
        except Exception as e:
            logger.error(f"Failed to copy file: {e}")
            return

        # Create companion action .md file
        file_size = source.stat().st_size
        action_md = self.needs_action / f"FILE_{safe_name}_{timestamp}.md"

        content = f"""---
type: file_drop
source: inbox
original_name: {source.name}
copied_to: {dest_file.name}
size_bytes: {file_size}
received: {datetime.now().isoformat()}
priority: P3
status: pending
---

## File Received: {source.name}

A new file was dropped into the `/Inbox` folder and requires processing.

| Field         | Value                     |
|---------------|---------------------------|
| File Name     | `{source.name}`           |
| Size          | {file_size:,} bytes       |
| Received      | {datetime.now().strftime("%Y-%m-%d %H:%M:%S")} |
| Copied To     | `{dest_file.name}`        |

## Suggested Actions

- [ ] Review the file contents
- [ ] Determine if action is required
- [ ] If task-related: create a Plan in `/Plans/`
- [ ] If no action needed: move to `/Done/`
- [ ] Update `Dashboard.md` with status

## Notes

_Add context or instructions here after reviewing._
"""
        action_md.write_text(content, encoding="utf-8")
        logger.info(f"Created action file: {action_md.name}")


def main():
    parser = argparse.ArgumentParser(
        description="AI Employee — File System Watcher (Bronze Tier)"
    )
    parser.add_argument(
        "--vault",
        type=str,
        default="./AI_Employee_Vault",
        help="Path to the Obsidian vault directory (default: ./AI_Employee_Vault)",
    )
    args = parser.parse_args()

    vault_path = Path(args.vault).resolve()
    inbox_path = vault_path / "Inbox"

    if not vault_path.exists():
        logger.error(f"Vault not found: {vault_path}")
        sys.exit(1)

    inbox_path.mkdir(parents=True, exist_ok=True)
    logger.info(f"Vault: {vault_path}")
    logger.info(f"Watching: {inbox_path}")
    logger.info("Drop files into /Inbox to trigger processing. Press Ctrl+C to stop.")

    event_handler = InboxEventHandler(vault_path)
    observer = Observer()
    observer.schedule(event_handler, str(inbox_path), recursive=False)
    observer.start()

    try:
        while observer.is_alive():
            observer.join(timeout=1)
    except KeyboardInterrupt:
        logger.info("Stopping watcher...")
        observer.stop()
    observer.join()
    logger.info("Watcher stopped.")


if __name__ == "__main__":
    main()
