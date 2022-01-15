import logging
import sys
from argparse import ArgumentParser

from Xlib import X, display

from .models import ClipboardData
from .xoperations import process_event_loop


logger = logging.getLogger()


def set_logger_settings(level_name: str) -> None:
    level = logging.getLevelName(level_name)
    logging.basicConfig(stream=sys.stdout, level=level)


def main() -> None:
    parser = ArgumentParser(
        "Monitors the access of other processes to the clipboard contents."
    )
    parser.add_argument("-l", "--loglevel", help="Choose the log level")
    args = parser.parse_args()
    if args.loglevel and args.loglevel in ["DEBUG", "INFO", "WARNING", "ERROR"]:
        set_logger_settings(args.loglevel)
    else:
        set_logger_settings("WARNING")

    logger.info("Initializing Xclient")
    d = display.Display()
    # Create ourselves a window and a property for the returned data
    w = d.screen().root.create_window(0, 0, 10, 10, 0, X.CopyFromParent)
    w.set_wm_name("clipboard_watcher")

    logger.debug("Getting selection data")
    cb_data = ClipboardData(d, w, {}, {})
    cb_data.refresh_all()
    logger.debug("Taken ownership of all selections")

    logger.info("Will start processing requests")
    process_event_loop(d, w, cb_data)


if __name__ == "__main__":
    main()
