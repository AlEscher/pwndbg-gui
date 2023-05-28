import logging
from typing import TYPE_CHECKING

from PySide6.QtCore import Qt, QProcess, QThread, Signal
from PySide6.QtWidgets import QTextEdit

from update_contexts import UpdateContexts

if TYPE_CHECKING:
    from gui import PwnDbgGui

logger = logging.getLogger(__file__)


class MainTextEdit(QTextEdit):
    do_work = Signal()

    def __init__(self, parent: 'PwnDbgGui', gdb: QProcess):
        super().__init__(parent)
        self.update_thread = QThread()
        self.update_worker = UpdateContexts(parent)
        self.gdb = gdb
        self.parent = parent
        self.start_update_worker()

    def start_update_worker(self):
        self.update_thread = QThread()
        self.update_worker = UpdateContexts(self.parent)
        self.update_worker.moveToThread(self.update_thread)
        # Allow the worker to update contexts in the GUI thread
        self.update_worker.update_context.connect(self.parent.update_context)
        self.do_work.connect(self.update_worker.update_contexts)
        self.update_thread.finished.connect(self.update_worker.deleteLater)
        logger.debug("Starting new worker thread in MainTextEdit")
        self.update_thread.start()

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Return or event.key() == Qt.Key_Enter:
            # Enter was pressed, send command to pwndbg
            self.submit_cmd()
        super().keyPressEvent(event)

    def submit_cmd(self):
        lines = self.toPlainText().splitlines(keepends=True)
        if len(lines) > 0:
            cmd = lines[-1]
            cmd = cmd[cmd.find(">") + 1:]
            logger.debug("Sending command '%s' to gdb from main text edit", cmd)
            self.gdb.write(cmd.encode())
            self.do_work.emit()
            return
        logger.debug("No lines to send as command!")
