"""
Local Agent Notifier

Handles desktop notifications for:
- New approval requests
- Execution completions
- System alerts
- Cloud sync updates
"""

import logging
import platform
import subprocess
from pathlib import Path
from datetime import datetime
from typing import Optional, List, Dict
from dataclasses import dataclass

from .config import LocalConfig, get_config

logger = logging.getLogger(__name__)


@dataclass
class Notification:
    """Represents a notification"""
    title: str
    message: str
    priority: str = "normal"  # low, normal, high, urgent
    category: str = "general"  # approval, execution, sync, alert
    timestamp: datetime = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()


class LocalNotifier:
    """
    Local Agent Notifier
    
    Cross-platform desktop notifications:
    - Windows: Toast notifications
    - macOS: NSUserNotification / osascript
    - Linux: notify-send (libnotify)
    """
    
    def __init__(self, config: Optional[LocalConfig] = None):
        self.config = config or get_config()
        self.notifications_sent: int = 0
        self.notification_history: List[Notification] = []
    
    def send(self, notification: Notification) -> bool:
        """Send a notification"""
        if not self.config.desktop_notifications:
            logger.debug(f"Notifications disabled, skipping: {notification.title}")
            return False
        
        try:
            # Determine OS and send appropriate notification
            system = platform.system()
            
            if system == "Windows":
                success = self._send_windows(notification)
            elif system == "Darwin":
                success = self._send_macos(notification)
            elif system == "Linux":
                success = self._send_linux(notification)
            else:
                logger.warning(f"Unknown OS: {system}")
                success = False
            
            if success:
                self.notifications_sent += 1
                self.notification_history.append(notification)
                
                # Play sound if enabled
                if self.config.notification_sound:
                    self._play_sound(notification.priority)
            
            return success
            
        except Exception as e:
            logger.error(f"Failed to send notification: {e}")
            return False
    
    def _send_windows(self, notification: Notification) -> bool:
        """Send Windows toast notification"""
        try:
            from win10toast import ToastNotifier
            
            toaster = ToastNotifier()
            
            # Map priority to duration
            duration_map = {
                "low": 5,
                "normal": 10,
                "high": 15,
                "urgent": 30,
            }
            duration = duration_map.get(notification.priority, 10)
            
            toaster.show_toast(
                notification.title,
                notification.message,
                duration=duration,
                threaded=True,
            )
            
            logger.debug(f"Windows notification sent: {notification.title}")
            return True
            
        except ImportError:
            logger.warning("win10toast not installed, falling back to print")
            print(f"📬 {notification.title}: {notification.message}")
            return True
        except Exception as e:
            logger.error(f"Windows notification failed: {e}")
            return False
    
    def _send_macos(self, notification: Notification) -> bool:
        """Send macOS notification using osascript"""
        try:
            # Escape quotes in message
            title_escaped = notification.title.replace('"', '\\"')
            message_escaped = notification.message.replace('"', '\\"')
            
            script = f'''
            display notification "{message_escaped}" with title "{title_escaped}"
            '''
            
            subprocess.run(
                ["osascript", "-e", script],
                capture_output=True,
                timeout=5,
            )
            
            logger.debug(f"macOS notification sent: {notification.title}")
            return True
            
        except Exception as e:
            logger.error(f"macOS notification failed: {e}")
            return False
    
    def _send_linux(self, notification: Notification) -> bool:
        """Send Linux notification using notify-send"""
        try:
            # Map priority to urgency
            urgency_map = {
                "low": "low",
                "normal": "normal",
                "high": "high",
                "urgent": "critical",
            }
            urgency = urgency_map.get(notification.priority, "normal")
            
            subprocess.run(
                [
                    "notify-send",
                    "-u", urgency,
                    "-a", "AI Employee",
                    notification.title,
                    notification.message,
                ],
                capture_output=True,
                timeout=5,
            )
            
            logger.debug(f"Linux notification sent: {notification.title}")
            return True
            
        except Exception as e:
            logger.error(f"Linux notification failed: {e}")
            return False
    
    def _play_sound(self, priority: str = "normal"):
        """Play notification sound"""
        try:
            system = platform.system()
            
            if system == "Windows":
                import winsound
                if priority in ["high", "urgent"]:
                    winsound.PlaySound("SystemExclamation", winsound.SND_ASYNC)
                else:
                    winsound.PlaySound("SystemNotification", winsound.SND_ASYNC)
            
            elif system == "Darwin":
                sound_file = "/System/Library/Sounds/Glass.aiff"
                if priority in ["high", "urgent"]:
                    sound_file = "/System/Library/Sounds/Submarine.aiff"
                subprocess.run(["afplay", sound_file], timeout=5)
            
            elif system == "Linux":
                sound_file = "/usr/share/sounds/freedesktop/stereo/message.oga"
                if priority in ["high", "urgent"]:
                    sound_file = "/usr/share/sounds/freedesktop/stereo/alarm-clock-elapsed.oga"
                subprocess.run(["paplay", sound_file], timeout=5)
        
        except Exception as e:
            logger.debug(f"Sound playback failed: {e}")
    
    def notify_approval_pending(self, count: int, action_types: List[str]):
        """Notify user of pending approvals"""
        notification = Notification(
            title="📋 Approval Required",
            message=f"{count} action(s) awaiting approval: {', '.join(action_types[:3])}",
            priority="high" if count > 5 else "normal",
            category="approval",
        )
        self.send(notification)
    
    def notify_execution_complete(self, action_type: str, success: bool):
        """Notify user of execution completion"""
        if success:
            notification = Notification(
                title="✅ Action Completed",
                message=f"{action_type} executed successfully",
                priority="low",
                category="execution",
            )
        else:
            notification = Notification(
                title="❌ Action Failed",
                message=f"{action_type} execution failed - check logs",
                priority="high",
                category="alert",
            )
        self.send(notification)
    
    def notify_sync_complete(self, status: str, changes: int):
        """Notify user of sync completion"""
        notification = Notification(
            title="🔄 Vault Synced",
            message=f"Sync status: {status} ({changes} changes)",
            priority="low",
            category="sync",
        )
        self.send(notification)
    
    def notify_error(self, error_message: str):
        """Notify user of system error"""
        notification = Notification(
            title="⚠️ System Alert",
            message=error_message,
            priority="urgent",
            category="alert",
        )
        self.send(notification)
    
    def notify_lead_detected(self, lead_priority: str, source: str):
        """Notify user of business lead detected"""
        emoji = "🎯" if lead_priority == "P1" else "📧"
        notification = Notification(
            title=f"{emoji} Business Lead Detected",
            message=f"High-priority lead from {source}",
            priority="high" if lead_priority == "P1" else "normal",
            category="alert",
        )
        self.send(notification)
    
    def get_statistics(self) -> Dict:
        """Get notification statistics"""
        return {
            "total_sent": self.notifications_sent,
            "history_count": len(self.notification_history),
            "enabled": self.config.desktop_notifications,
            "sound_enabled": self.config.notification_sound,
        }
    
    def get_history(self, limit: int = 50) -> List[Notification]:
        """Get recent notification history"""
        return self.notification_history[-limit:]
    
    def clear_history(self):
        """Clear notification history"""
        self.notification_history = []
        logger.info("Notification history cleared")


def create_notifier(config: Optional[LocalConfig] = None) -> LocalNotifier:
    """Create LocalNotifier instance"""
    return LocalNotifier(config)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    config = get_config()
    notifier = create_notifier(config)
    
    # Test notifications
    notifier.send(Notification(
        title="Test Notification",
        message="This is a test from Local Agent Notifier",
        priority="normal",
    ))
    
    # Test approval notification
    notifier.notify_approval_pending(3, ["email_send", "social_post", "payment"])
    
    # Show statistics
    stats = notifier.get_statistics()
    logger.info(f"Notification statistics: {stats}")
