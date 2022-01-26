import dbus
import logging

logger = logging.getLogger("ClipboardWatcher")


def display_desktop_notification(title: str, details: str = "", icon: str = "") -> None:
    interface = "org.freedesktop.Notifications"
    path = "/org/freedesktop/Notifications"
    notification = dbus.Interface(
        dbus.SessionBus().get_object(interface, path), interface
    )
    try:
        notification.Notify("Clipboard-Watcher", 0, icon, title, details, [], [], 7000)
    except Exception:
        logger.error("Unable to publish notification due to dbus error")
