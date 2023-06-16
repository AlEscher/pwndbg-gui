import logging
import os
import select
from typing import TYPE_CHECKING

from PySide6.QtCore import QObject, Slot, Signal

# Prevent circular import error
if TYPE_CHECKING:
    from gui import PwnDbgGui

logger = logging.getLogger(__file__)


class UpdateContexts(QObject):
    update_context = Signal(str, str)

    def __init__(self, gui: 'PwnDbgGui'):
        super().__init__()
        self.gui = gui

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
                    self.update_context.emit(segment, content)
                else:
                    logger.debug("No available data to read from %s", pipe_path)
                os.close(pipe)
            except OSError as e:
                logger.debug(e)
        self.gui.gdb.waitForReadyRead()
        logger.debug("Reading stdout from GDB with state %s", self.gui.gdb.state())
        content = self.gui.gdb.readAllStandardOutput()
        self.update_context.emit("main", content.data().decode())
        logger.info("Finished reading data for contexts")
