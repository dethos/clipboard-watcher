from dataclasses import dataclass
from typing import Optional, Any, Dict, List
import logging

from Xlib import X

from .xoperations import get_selection_data, get_selection_targets

logger = logging.getLogger("ClipboardWatcher")


@dataclass
class SelectionValue:
    value: Optional[Any]  # TODO figure out later
    format: Optional[int]
    type: Optional[Any]  # TODO must figure later


@dataclass
class SelectionTarget:
    target: str
    data: SelectionValue


@dataclass
class ClipboardData:
    display: Any  # TODO Add types later
    window: Any  # TODO Add types later
    primary: Dict[str, SelectionTarget]
    clipboard: Dict[str, SelectionTarget]

    def _refresh_selection(
        self, selection: str, content: Dict[str, SelectionTarget]
    ) -> None:
        targets = get_selection_targets(self.display, self.window, selection)
        logger.debug("Got %s for selection %s", targets, selection)
        for target in targets:
            if target in ["TARGETS", "SAVE_TARGETS"]:
                continue
            data = get_selection_data(self.display, self.window, selection, target)
            if data:
                value = SelectionValue(*data)
                content[target] = SelectionTarget(target, value)

    def refresh_primary(self) -> None:
        selection = "PRIMARY"
        sel_atom = self.display.get_atom(selection)
        self.primary = {}
        self._refresh_selection(selection, self.primary)
        self.window.set_selection_owner(sel_atom, X.CurrentTime)

    def refresh_clipboard(self) -> None:
        selection = "CLIPBOARD"
        sel_atom = self.display.get_atom(selection)
        self.clipboard = {}
        self._refresh_selection(selection, self.clipboard)
        self.window.set_selection_owner(sel_atom, X.CurrentTime)

    def refresh_all(self) -> None:
        self.refresh_primary()
        self.refresh_clipboard()

    def name_atoms(self, d) -> List[str]:
        return [d.get_atom(sel) for sel in ["PRIMARY", "CLIPBOARD"]]
