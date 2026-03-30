"""
base_watcher.py - Abstract base class for all AI Employee watchers.

All watchers inherit from BaseWatcher and implement:
  - check_for_updates() -> list of new items
  - create_action_file(item) -> Path to created .md file
"""

import time
import logging
from pathlib import Path
from abc import ABC, abstractmethod

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)


class BaseWatcher(ABC):
    """Base class for all Watcher scripts."""

    def __init__(self, vault_path: str, check_interval: int = 60):
        self.vault_path = Path(vault_path)
        self.needs_action = self.vault_path / "Needs_Action"
        self.check_interval = check_interval
        self.logger = logging.getLogger(self.__class__.__name__)

        # Ensure Needs_Action folder exists
        self.needs_action.mkdir(parents=True, exist_ok=True)

    @abstractmethod
    def check_for_updates(self) -> list:
        """Return a list of new items to process."""
        pass

    @abstractmethod
    def create_action_file(self, item) -> Path:
        """Create a .md action file in Needs_Action and return its path."""
        pass

    def run(self):
        """Main loop: poll for updates and create action files."""
        self.logger.info(f"Starting {self.__class__.__name__} (interval: {self.check_interval}s)")
        while True:
            try:
                items = self.check_for_updates()
                if items:
                    self.logger.info(f"Found {len(items)} new item(s) to process.")
                for item in items:
                    path = self.create_action_file(item)
                    self.logger.info(f"Created action file: {path}")
            except KeyboardInterrupt:
                self.logger.info("Watcher stopped by user.")
                break
            except Exception as e:
                self.logger.error(f"Unexpected error: {e}", exc_info=True)
            time.sleep(self.check_interval)
