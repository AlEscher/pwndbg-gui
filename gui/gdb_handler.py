import logging
import os
import select
import gdb
from typing import TYPE_CHECKING, List

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
        response = gdb.execute(cmd, to_string=True)
        logger.debug(response[:100])
        self.update_gui.emit("main", response.encode())

    @Slot()
    def update_contexts(self):
        logger.info("Starting updating contexts")
        '''
        for segment, pipe_path in self.gui.pipes.items():
            try:
                pipe = os.open(pipe_path, os.O_RDONLY | os.O_NONBLOCK)
                # if pipe in select.select([pipe], [], [], 0)[0]:
                content = os.read(pipe, 64000)
                if content != b"":
                    logger.debug("Reading from %s at %s", segment, pipe_path)
                    logger.debug("Writing to %s", self.gui.seg_to_widget[segment].objectName())
                    self.update_gui.emit(segment, content)
                else:
                    logger.debug("No available data to read from %s", pipe_path)
                os.close(pipe)
            except OSError as e:
                logger.debug(e)
        '''
        logger.debug("Reading stdout from GDB with state %s", self.gdb.state())
        content_read: List[bytes] = []
        content = b""
        while b"pwndbg>" not in content:
            if not self.gdb.waitForReadyRead(2000):
                break
            content = self.gdb.readAllStandardOutput().data()
            content_read.append(content)
        self.update_gui.emit("main", b"".join(content_read))
        logger.info("Finished reading data for contexts")

    @Slot()
    def start_gdb(self, arguments: List[str]):
        """Runs gdb with the given program and waits for gdb to have started"""
        logger.info("Setting GDB target to %s", arguments)
        cmd = "file " + " ".join(arguments)
        gdb.execute(cmd)
