import logging
from typing import TYPE_CHECKING, List

import gdb
from PySide6.QtCore import QObject, Slot, Signal, QProcess

# Prevent circular import error
if TYPE_CHECKING:
    from gui import PwnDbgGui

logger = logging.getLogger(__file__)


class GdbHandler(QObject):
    update_gui = Signal(str, bytes)

    def __init__(self, gui: 'PwnDbgGui'):
        super().__init__()
        self.gui = gui
        self.gdb: QProcess | None = None
        self.past_commands: List[str] = []

    @Slot()
    def send_command(self, cmd: str):
        response = gdb.execute(cmd, from_tty=True, to_string=True)
        self.update_gui.emit("main", response.encode())

    @Slot()
    def start_gdb(self, arguments: List[str]):
        """Runs gdb with the given program and waits for gdb to have started"""
        logger.info("Setting GDB target to %s", arguments)
        cmd = "file " + " ".join(arguments)
        gdb.execute(cmd)
