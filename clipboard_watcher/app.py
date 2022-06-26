"""Main script to execute the application

This module provides the entrypoint to CLI app/script
"""
import logging
import sys
from argparse import ArgumentParser
from threading import Thread
from queue import Queue

from Xlib import X, display

from .models import ClipboardData
from .xoperations import process_event_loop
from .notifications import display_desktop_notification


logger = logging.getLogger("ClipboardWatcher")


def set_logger_settings(level_name: str) -> None:
    level = logging.getLevelName(level_name)
    logging.basicConfig(stream=sys.stdout, level=level)


def process_notifications(q: Queue):
    while True:
        req = q.get(block=True)
        window_info = f"Window info: {req['window_name']} (id: {req['id']})"
        if process := req.get("process"):
            process_info = f"Process info: {process.path} (pid: {process.pid})"
        else:
            process_info = "Process info: Unknown"

        display_desktop_notification(
            f"Access to Clipboard ({req['selection']}) detected.",
            f"{window_info}\n{process_info}",
        )


def main() -> None:
    parser = ArgumentParser(
        "Monitors the access of other processes to the clipboard contents."
    )
    parser.add_argument("-l", "--loglevel", help="Choose the log level")
    parser.add_argument(
        "-p",
        "--permission",
        action="store_true",
        help="Ask for permission before sending clipboard data",
    )
    args = parser.parse_args()
    if args.loglevel and args.loglevel in ["DEBUG", "INFO", "WARNING", "ERROR"]:
        set_logger_settings(args.loglevel)
    else:
        set_logger_settings("INFO")

    logger.info("Initializing X client")
    disp = display.Display()
    # Create ourselves a window and a property for the returned data
    window = disp.screen().root.create_window(0, 0, 10, 10, 0, X.CopyFromParent)
    window.set_wm_name("clipboard_watcher")

    logger.debug("Getting selection data")
    cb_data = ClipboardData(disp, window, {}, {})
    cb_data.refresh_all()
    logger.debug("Taken ownership of all selections")

    job_queue = Queue()
    # Thread 1
    event_worker = Thread(
        target=process_event_loop,
        args=(disp, window, job_queue, cb_data, args.permission),
        daemon=True,
    )
    # Thread 2
    notif_worker = Thread(
        target=process_notifications,
        args=(job_queue,),
        daemon=True,
    )

    event_worker.start()
    notif_worker.start()
    logger.info("Setup done. Keeping an eye on the clipboard")
    try:
        event_worker.join()
        notif_worker.join()
    except KeyboardInterrupt:
        logger.info("Shutting down")


if __name__ == "__main__":
    main()
