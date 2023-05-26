import logging
import os
from typing import TYPE_CHECKING

from PySide6.QtCore import QObject, Slot, Signal


if TYPE_CHECKING:
    from gui import PwnDbgGui

logger = logging.getLogger(__file__)


class UpdateContexts(QObject):
    finished = Signal()
    progress = Signal(int)

    def __init__(self, gui: 'PwnDbgGui'):
        super().__init__()
        self.gui = gui

    @Slot()
    def update_contexts(self):
        for segment, (_, slave) in self.gui.ttys.items():
            logger.debug("Reading from %s at %s", segment, os.ttyname(slave))
            content = os.read(slave, 4096)
            logger.debug("Writing to %s", self.gui.seg_to_widget[segment].objectName())
            self.gui.seg_to_widget[segment].setText(content.decode())
        self.finished.emit()
