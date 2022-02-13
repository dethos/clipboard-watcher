"""Process Info Module

This module provides the tools to fetch all the necessary information
about running processes.

It is used to populate the information displayed to the user about who
is accessing the clipboard information.
"""
from __future__ import annotations
from datetime import datetime
from typing import Optional
from dataclasses import dataclass
from pathlib import Path

import psutil


@dataclass()
class ProcessInfo:
    pid: int
    name: Optional[str]
    path: Optional[Path]

    parent: int
    user: str
    started_at: Optional[datetime]

    @classmethod
    def collect(cls, pid: int) -> ProcessInfo:
        p = psutil.Process(pid)
        details = p.as_dict(
            attrs=["ppid", "exe", "create_time", "name", "username"], ad_value=None
        )

        if timestamp := details.get("create_time"):
            date = datetime.fromtimestamp(timestamp)
        else:
            date = None

        if exe := details.get("exe"):
            path = Path(exe)
        else:
            path = None

        return cls(
            pid,
            details["name"],
            path,
            details["ppid"],
            details["username"],
            date,
        )
