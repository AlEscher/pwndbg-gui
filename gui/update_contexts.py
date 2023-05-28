import logging
import os
import select
from typing import TYPE_CHECKING

from PySide6.QtCore import QObject, Slot, Signal


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
        for segment, (master, _) in self.gui.ttys.items():
            try:
                if not select.select([master], [], [], 0)[0]:
                    logger.debug("No data readable for %s at %s", segment, os.ttyname(master))
                    continue
                logger.debug("Reading from %s at %s", segment, os.ttyname(master))
                content = os.read(master, 4096)
                logger.debug("Writing to %s", self.gui.seg_to_widget[segment].objectName())
                self.update_context.emit(segment, content.decode())
            except OSError as e:
                logger.debug(e)
        logger.debug("Reading stdout from GDB")
        content = self.gui.gdb.readAll()
        self.update_context.emit("main", content.data().decode())
        logger.info("Finished reading data for contexts")
