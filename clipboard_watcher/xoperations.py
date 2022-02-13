"""X Operations Module

This module abstracts some of the functionality of Xlib into
easy to use functions.

The current functionality contains:
* Querying the existing clipboard targets
* Fetching existing clipboard data
* Processing requests for clipboard data
* Handling the loss of ownership on any clipboard data
"""

import logging
from typing import List, Optional, Tuple
from queue import Queue

from Xlib import X, Xatom
from Xlib.ext.res import query_client_ids, LocalClientPIDMask
from Xlib.protocol import event

from .process_info import ProcessInfo

logger = logging.getLogger("ClipboardWatcher")


def get_selection_targets(disp, win, selection: str) -> List[str]:
    """Query a selection owner for a list of all available targets."""
    data_info = get_selection_data(disp, win, selection, "TARGETS")
    if not data_info or data_info[1] != 32 and data_info[2] != Xatom.ATOM:
        return []

    data, *_ = data_info
    return [disp.get_atom_name(a) for a in data]


def get_selection_data(disp, win, selection: str, target: str) -> Optional[Tuple]:
    """Retrieve the data for a given target from the selection owner."""
    sel_atom = disp.get_atom(selection)
    target_atom = disp.get_atom(target)
    data_atom = disp.get_atom("SEL_DATA")

    # Ask the server who owns this selection, if any
    owner = disp.get_selection_owner(sel_atom)
    if owner == X.NONE:
        logger.info("No owner for selection %s", selection)
        return

    win.convert_selection(sel_atom, target_atom, data_atom, X.CurrentTime)

    # Wait for the notification that we got the selection
    while True:
        e = disp.next_event()
        if e.type == X.SelectionNotify:
            break

    # Do some sanity checks
    if e.requestor != win or e.selection != sel_atom or e.target != target_atom:
        logger.info("SelectionNotify event does not match our request: %s", e)

    if e.property == X.NONE:
        logger.info("Selection lost or conversion to TEXT failed")
        return

    if e.property != data_atom:
        logger.info("SelectionNotify event does not match our request: %s", e)

    # Get the data
    r = win.get_full_property(data_atom, X.AnyPropertyType, sizehint=10000)
    if not r:
        return

    # Can the data be used directly or read incrementally
    if r.property_type == disp.get_atom("INCR"):
        logger.info("Reading data incrementally: at least %d bytes", r.value[0])
        data = _handle_incr(disp, win, data_atom)
    else:
        data = r.value

    # Tell selection owner that we're done
    win.delete_property(data_atom)
    return (data, r.format, r.property_type)


def _handle_incr(d, w, data_atom) -> bytes:
    """Handle the selection's data, when it is provided in chunks"""
    w.change_attributes(event_mask=X.PropertyChangeMask)
    data = None

    while True:
        # Delete data property to tell owner to give us more data
        w.delete_property(data_atom)
        # Wait for notification that we got data
        while True:
            e = d.next_event()
            if (
                e.type == X.PropertyNotify
                and e.state == X.PropertyNewValue
                and e.window == w
                and e.atom == data_atom
            ):
                break

        r = w.get_full_property(data_atom, X.AnyPropertyType, sizehint=10000)

        # End of data
        if len(r.value) == 0:
            return data

        if not data:
            data = e.value
            continue

        data += r.value


def process_selection_request_event(d, cb_data, e) -> None:
    logger.debug("Selection %s request from %s", e.selection, e.requestor.get_wm_name())
    client = e.requestor
    targets_atom = d.get_atom("TARGETS")

    if e.property == X.NONE:
        logger.info("request from obsolete client!")
        client_prop = e.target
    else:
        client_prop = e.property

    target_name = d.get_atom_name(e.target)

    logger.info(
        "got request for %s, dest %s on %d %s",
        target_name,
        d.get_atom_name(client_prop),
        client.id,
        client.get_wm_name(),
    )

    if e.selection == d.get_atom("PRIMARY"):
        if target_name == "TARGETS":
            atoms = [d.get_atom(name) for name in cb_data.primary.keys()]
            prop = {
                "value": [targets_atom] + atoms,
                "format": 32,
                "type": Xatom.ATOM,
            }
        elif target_name in cb_data.primary.keys():
            cb_values = cb_data.primary[target_name].data
            prop = {
                "value": cb_values.value,
                "format": cb_values.format,
                "type": cb_values.type,
            }
        else:
            logger.warning("Invalid target")
            client_prop = X.NONE
            prop = None
    elif e.selection == d.get_atom("CLIPBOARD"):
        if target_name == "TARGETS":
            atoms = [d.get_atom(name) for name in cb_data.clipboard.keys()]
            prop = {
                "value": [targets_atom] + atoms,
                "format": 32,
                "type": Xatom.ATOM,
            }
        elif target_name in cb_data.clipboard.keys():
            cb_values = cb_data.clipboard[target_name].data
            prop = {
                "value": cb_values.value,
                "format": cb_values.format,
                "type": cb_values.type,
            }
        else:
            logger.info("Received selection request for invalid target")
            client_prop = X.NONE
            prop = None
    else:
        logger.info("Received event for other selection")
        client_prop = X.NONE
        prop = None

    if client_prop != X.NONE:
        if prop is not None:
            client.change_property(
                client_prop, prop["type"], prop["format"], prop["value"]
            )

    # And always send a selection notification
    ev = event.SelectionNotify(
        time=e.time,
        requestor=e.requestor,
        selection=e.selection,
        target=e.target,
        property=client_prop,
    )

    client.send_event(ev)
    logger.warning(
        "Sent %s (target: %s) selection to %s (%s)",
        d.get_atom_name(e.selection),
        target_name,
        e.requestor.get_wm_name(),
        e.requestor.id,
    )


def process_selection_clear_event(d, cb_data, e) -> None:
    logger.warning("New content on %s, assuming ownership", d.get_atom_name(e.atom))
    if e.atom == d.get_atom("PRIMARY"):
        cb_data.refresh_primary()
    elif e.atom == d.get_atom("CLIPBOARD"):
        cb_data.refresh_clipboard()
    else:
        return

    logger.warning("Owner again")


def process_event_loop(d, w, q: Queue, cb_data) -> None:
    while True:
        e = d.next_event()
        if (
            e.type == X.SelectionRequest
            and e.owner == w
            and e.selection in cb_data.name_atoms(d)
        ):
            req_id = e.requestor.id
            req_name = e.requestor.get_wm_name()
            client_ids = query_client_ids(d, [(e.requestor.id, LocalClientPIDMask)])
            client_id = client_ids.ids[0]

            req_pid = e.requestor.get_property(
                d.get_atom("_NET_WM_PID"), d.get_atom("CARDINAL"), 0, 1024
            )
            if client_id.spec.mask & LocalClientPIDMask:
                req_pid = client_id.value[0]

            # We must collect this information before processing the request
            # due to the risk of the requestor no longer be running afterwards
            proc_info = ProcessInfo.collect(req_pid) if req_pid else None

            process_selection_request_event(d, cb_data, e)
            if d.get_atom_name(e.target) != "TARGETS":
                q.put(
                    {
                        "id": req_id,
                        "window_name": req_name,
                        "process": proc_info,
                        "target": d.get_atom_name(e.target),
                        "selection": d.get_atom_name(e.selection),
                    },
                    block=False,
                )

        elif e.type == X.SelectionClear and e.window == w:
            process_selection_clear_event(d, cb_data, e)
