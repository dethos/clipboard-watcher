from desktop_notifier import DesktopNotifier
import logging

logger = logging.getLogger("ClipboardWatcher")
notifier = DesktopNotifier(app_name="Clipboard-Watcher", app_icon=None)


def display_desktop_notification(title: str, details: str = "") -> None:
    try:
        notifier.send_sync(title=title, message=details)
    except Exception:
        logger.error("Unable to publish notification due to dbus error")
