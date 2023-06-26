import logging
from typing import List

import time

# These imports are broken here, but will work via .gdbinit
import gdb
from PySide6.QtCore import QObject, Slot, Signal

import os
import fcntl

from gui.inferior_state import InferiorState

logger = logging.getLogger(__file__)


class InferiorHandler(QObject):
    update_gui = Signal(str, bytes)
    INFERIOR_STATE = InferiorState.EXITED

    def __init__(self):
        super().__init__()

        # open a tty for interaction with the inferior process (allows for separation of contexts)
        self.master, self.slave = os.openpty()
        # Set the master file descriptor to non-blocking mode
        flags = fcntl.fcntl(self.master, fcntl.F_GETFL)
        fcntl.fcntl(self.master, fcntl.F_SETFL, flags | os.O_NONBLOCK)
        # execute gdb tty command to forward the inferior to this tty
        tty = os.ttyname(self.slave)
        logger.debug("Opened tty for inferior interaction: %s", tty)
        gdb.execute('tty ' + tty)

    @Slot()
    def inferior_read(self):
        logger.debug("Reading from inferior")
        while InferiorHandler.INFERIOR_STATE == InferiorState.RUNNING:
            try:
                inferior_read = os.read(self.master, 4096)
                if not inferior_read:
                    # End-of-file condition reached
                    break
                self.update_gui.emit("main", inferior_read)
            except BlockingIOError:
                # No data available currently
                time.sleep(0.2)
                continue
        try:
            inferior_read = os.read(self.master, 4096)
            self.update_gui.emit("main", inferior_read)
        except BlockingIOError:
            pass

    @Slot(bytes)
    def inferior_write(self, inferior_input: bytes):
        logger.debug("Writing %s to inferior", inferior_input.decode())
        os.write(self.master, inferior_input)
