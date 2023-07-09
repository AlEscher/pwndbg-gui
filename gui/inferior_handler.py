import fcntl
import logging
import os
import select
import tty

from PySide6.QtCore import QObject, Slot, Signal, QCoreApplication

from gui.inferior_state import InferiorState

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
        # Disable ASCII control character interpretation, so that any byte input by the user doesn't get swallowed
        tty.setraw(self.slave)
        tty.setraw(self.master)
        # execute gdb tty command to forward the inferior to this tty
        self.tty = os.ttyname(self.slave)
        logger.debug("Opened tty for inferior interaction: %s", self.tty)
        self.to_write = b""
        self.run = True

    @Slot()
    def inferior_runs(self):
        """Main entry for inferior thread. Read and Write to tty."""
        logger.debug("Starting Inferior Interaction")
        while self.run:
            can_read, _, _ = select.select([self.master], [], [], 0.2)  # Non-blocking check for readability
            if can_read:
                # read data and send it to main
                data = os.read(self.master, 4096)
                self.update_gui.emit("main", data)
            QCoreApplication.processEvents()  # Process pending write events
            if self.to_write != b"":
                os.write(self.master, self.to_write)
                self.to_write = b""

    @Slot(bytes)
    def inferior_write(self, inferior_input: bytes):
        """Inferior write slot. Will be emitted from gdb_handler.
        :param inferior_input: Bytes to write to the inferior
        """
        self.to_write += inferior_input

    @Slot()
    def set_run(self, state: bool) -> object:
        """Sets whether the thread should keep working"""
        self.run = state
