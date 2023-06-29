import logging
from typing import List

import time

# These imports are broken here, but will work via .gdbinit
from PySide6.QtCore import QObject, Slot, Signal, QCoreApplication

import os
import fcntl
import select

from inferior_state import InferiorState

logger = logging.getLogger(__file__)


class InferiorHandler(QObject):
    update_gui = Signal(str, bytes)
    INFERIOR_STATE = InferiorState.QUEUED

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
        # gdb.execute('tty ' + tty)

        self.to_write = b""

    @Slot()
    def inferior_runs(self):
        # logger.debug("Starting Inferior Interaction")
        while InferiorHandler.INFERIOR_STATE == InferiorState.RUNNING:
            time.sleep(0.2)
            can_read, _, _ = select.select([self.master], [], [], 0)  # Non-blocking check for readability
            if can_read:
                data = os.read(self.master, 4096)
                # Perform further processing on the data
                self.update_gui.emit("main", data)
            QCoreApplication.processEvents()  # Process pending write events
            if self.to_write != b"":
                # logger.debug("Writing %s to inferior", self.to_write.decode())
                os.write(self.master, self.to_write)
                self.to_write = b""


    @Slot(bytes)
    def inferior_write(self, inferior_input: bytes):
        self.to_write += inferior_input
