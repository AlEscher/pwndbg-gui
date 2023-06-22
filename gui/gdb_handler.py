import logging
import os
import select
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
        self.gdb.write(cmd.encode() + b"\n")
        self.past_commands.append(cmd)

    @Slot()
    def update_contexts(self):
        logger.info("Starting updating contexts")
        for segment, pipe_path in self.gui.pipes.items():
            try:
                pipe = os.open(pipe_path, os.O_RDONLY | os.O_NONBLOCK)
                if pipe in select.select([pipe], [], [], 0)[0]:
                    logger.debug("Reading from %s at %s", segment, pipe_path)
                    content = os.read(pipe, 4096)
                    logger.debug("Writing to %s", self.gui.seg_to_widget[segment].objectName())
                    self.update_gui.emit(segment, content)
                else:
                    logger.debug("No available data to read from %s", pipe_path)
                os.close(pipe)
            except OSError as e:
                logger.debug(e)
        logger.debug("Reading stdout from GDB with state %s", self.gdb.state())
        content_read: List[bytes] = []
        content = b""
        while b"pwndbg>" not in content:
            if not self.gdb.waitForReadyRead(1000):
                break
            content = self.gdb.readAllStandardOutput().data()
            logger.debug(content)
            content_read.append(content)
        self.update_gui.emit("main", b"".join(content_read))
        logger.info("Finished reading data for contexts")

    @Slot()
    def start_gdb(self, argument: str):
        """Runs gdb with the given program and waits for gdb to have started"""
        logger.info("Starting GDB process with target %s", argument)
        self.gdb = QProcess()
        self.gdb.setProgram("gdb")
        self.gdb.setArguments([argument])
        self.gdb.setProcessChannelMode(QProcess.ProcessChannelMode.MergedChannels)
        self.gdb.start()
        self.gdb.waitForStarted()
        logger.info("GDB running with state %s", self.gdb.state())

    @Slot()
    def stop_gdb(self):
        logger.info("Closing GDB process")
        self.gdb.close()
        self.gdb.waitForFinished()
        logger.debug("Waited for GDB process with current state: %s", self.gdb.state())
