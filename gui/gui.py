# This Python file uses the following encoding: utf-8
import logging
import sys
from pathlib import Path

import PySide6
from PySide6.QtCore import QProcess, Slot
from PySide6.QtGui import QTextOption
from PySide6.QtWidgets import QApplication, QWidget, QFileDialog, QTextBrowser, QTextEdit

from main_text_edit import MainTextEdit
from pty_util import close_pty_pair, create_pty_devices
# Important:
# You need to run the following command to generate the ui_form.py file
#     pyside6-uic form.ui -o ui_form.py, or
#     pyside2-uic form.ui -o ui_form.py
from ui_form import Ui_PwnDbgGui

logger = logging.getLogger(__file__)


class PwnDbgGui(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.gdbinit = Path.home() / ".gdbinit"
        self.gdbinit_backup = self.gdbinit.read_bytes()
        self.gdb: QProcess | None = None
        logger.info("Creating PTY devices")
        ttys = create_pty_devices(["stack"])
        self.ttys = ttys
        self.ui = Ui_PwnDbgGui()
        self.ui.setupUi(self)
        self.ui.file_button.clicked.connect(self.file_button_clicked)
        self.seg_to_widget = dict(stack=self.ui.stack)

    def start_gdb(self, debugee: str):
        """Runs gdb with the given program and waits for gdb to have started"""
        logger.info("Starting GDB process with target %s", debugee)
        self.gdb = QProcess()
        self.gdb.setProgram("gdb")
        self.gdb.setArguments(debugee)
        self.gdb.start()
        self.gdb.waitForStarted()
        logger.info("GDB running with state %s", self.gdb.state())
        # Replace the "Main" widget with our custom implementation
        main_text_edit = MainTextEdit(parent=self, gdb=self.gdb)
        self.ui.splitter.replaceWidget(0, main_text_edit)
        self.seg_to_widget["main"] = main_text_edit
        self.seg_to_widget["main"].do_work.emit()

    def closeEvent(self, event: PySide6.QtGui.QCloseEvent) -> None:
        """Called when window is closed. Cleanup all ptys and terminate the gdb process"""
        logger.debug("Resetting gdbinit")
        self.gdbinit.write_bytes(self.gdbinit_backup)
        map(close_pty_pair, self.ttys.values())
        if self.gdb:
            logger.debug("Stopping MainTextEdit update thread")
            self.seg_to_widget["main"].stop_thread.emit()
            logger.info("Closing GDB process")
            self.gdb.close()
            self.gdb.waitForFinished()
            logger.debug("Waited for GDB process with current state: %s", self.gdb.state())

    @Slot()
    def file_button_clicked(self):
        dialog = QFileDialog(self)
        dialog.setFileMode(QFileDialog.ExistingFile)
        dialog.setViewMode(QFileDialog.Detail)
        if dialog.exec() and len(dialog.selectedFiles()) > 0:
            file_name = dialog.selectedFiles()[0]
            self.start_gdb(file_name)

    @Slot(str, str)
    def update_context(self, context: str, content: str):
        widget: QTextEdit | QTextBrowser = self.seg_to_widget[context]
        logger.debug("Updating context %s with \"%s...\"", widget.objectName(), content[:100])
        widget.setText(content)


def run_gui():
    app = QApplication(sys.argv)
    widget = PwnDbgGui()
    widget.show()
    sys.exit(app.exec())
