import logging
from typing import TYPE_CHECKING, List

from PySide6.QtCore import Qt, QProcess, QThread, Signal
from PySide6.QtWidgets import QTextEdit

from gdb_handler import GdbHandler

# Prevent circular import error
if TYPE_CHECKING:
    from gui import PwnDbgGui

logger = logging.getLogger(__file__)


class MainTextEdit(QTextEdit):
    gdb_read = Signal()
    gdb_write = Signal(str)
    gdb_stop = Signal()
    gdb_start = Signal(str)
    stop_thread = Signal()

    def __init__(self, parent: 'PwnDbgGui', debugee: str):
        super().__init__(parent)
        self.update_thread = QThread()
        self.update_worker = GdbHandler(parent)
        self.parent = parent
        self.setObjectName("main")
        self.start_update_worker(debugee)

    def start_update_worker(self, debugee: str):
        self.update_thread = QThread()
        self.update_worker = GdbHandler(self.parent)
        self.update_worker.moveToThread(self.update_thread)
        # Allow the worker to update contexts in the GUI thread
        self.update_worker.update_gui.connect(self.parent.update_pane)
        # Allow giving the thread work from outside
        self.gdb_read.connect(self.update_worker.update_contexts)
        self.gdb_write.connect(self.update_worker.send_command)
        # Thread cleanup
        self.update_thread.finished.connect(self.update_worker.deleteLater)
        # Allow stopping the thread from outside
        self.stop_thread.connect(self.update_thread.quit)
        self.gdb_stop.connect(self.update_worker.stop_gdb)
        logger.debug("Starting new worker thread in MainTextEdit")
        self.update_thread.start()
        self.gdb_start.connect(self.update_worker.start_gdb)
        self.gdb_start.emit(debugee)

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Return or event.key() == Qt.Key_Enter:
            # Enter was pressed, send command to pwndbg
            self.submit_cmd()
        super().keyPressEvent(event)

    def submit_cmd(self):
        lines = self.toPlainText().splitlines(keepends=True)
        if len(lines) > 0:
            cmd = lines[-1]
            cmd = cmd[cmd.find(">") + 17:]
            logger.debug("Sending command '%s' to gdb", cmd)
            self.gdb_write.emit(cmd)
            self.gdb_read.emit()
            return
        logger.debug("No lines to send as command!")
