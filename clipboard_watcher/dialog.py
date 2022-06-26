from tkinter.messagebox import askokcancel


def ask_for_permission(window_name, pid, path) -> bool:
    details = f"The process {pid} ({path}) with the window named '{window_name}' wants to access your clipboard data."
    return askokcancel("Clipboard-Watcher", details)
