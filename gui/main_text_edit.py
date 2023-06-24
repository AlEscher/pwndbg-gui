import logging
from typing import TYPE_CHECKING, List

from PySide6.QtCore import Qt, QThread, Signal
from PySide6.QtWidgets import QTextEdit

from gui.custom_widgets.context_text_edit import ContextTextEdit
from gui.gdb_handler import GdbHandler

# Prevent circular import error
if TYPE_CHECKING:
    from gui.gui import PwnDbgGui

logger = logging.getLogger(__file__)


class MainTextEdit(ContextTextEdit):
    gdb_write = Signal(str)
    gdb_start = Signal(list)
    stop_thread = Signal()

    def __init__(self, parent: 'PwnDbgGui', args: List[str]):
        super().__init__(parent)
        self.update_thread = QThread()
        self.gdb_handler = GdbHandler(active_contexts=parent.seg_to_widget.keys())
        self.parent = parent
        self.setObjectName("main")
        self.start_update_worker(args)

    def start_update_worker(self, args: List[str]):
        self.update_thread = QThread()
        self.gdb_handler.moveToThread(self.update_thread)
        # Allow the worker to update contexts in the GUI thread
        self.gdb_handler.update_gui.connect(self.parent.update_pane)
        # Allow giving the thread work from outside
        self.gdb_write.connect(self.gdb_handler.send_command)
        # Thread cleanup
        self.update_thread.finished.connect(self.gdb_handler.deleteLater)
        # Allow stopping the thread from outside
        self.stop_thread.connect(self.update_thread.quit)
        logger.debug("Starting new worker thread in MainTextEdit")
        self.update_thread.start()
        self.gdb_start.connect(self.gdb_handler.set_target)
        self.gdb_start.emit(args)

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Return or event.key() == Qt.Key_Enter:
            # Enter was pressed, send command to pwndbg
            self.submit_cmd()
        super().keyPressEvent(event)

    def submit_cmd(self):
        lines = self.toPlainText().splitlines(keepends=True)
        if len(lines) > 0:
            cmd = lines[-1]
            cmd = cmd[cmd.find(">")+1:]
            logger.debug("Sending command '%s' to gdb", cmd)
            self.gdb_write.emit(cmd)
            return
        logger.debug("No lines to send as command!")
