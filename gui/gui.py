# This Python file uses the following encoding: utf-8
import logging
import os
import sys
from typing import Tuple, Dict

import PySide6
from PySide6.QtCore import QProcess, Slot
from PySide6.QtWidgets import QApplication, QWidget, QFileDialog

from main_text_edit import MainTextEdit
from pty_util import close_pty_pair
# Important:
# You need to run the following command to generate the ui_form.py file
#     pyside6-uic form.ui -o ui_form.py, or
#     pyside2-uic form.ui -o ui_form.py
from ui_form import Ui_PwnDbgGui

logger = logging.getLogger(__file__)


class PwnDbgGui(QWidget):
    def __init__(self, ttys: Dict[str, Tuple[int, int]], parent=None):
        super().__init__(parent)
        self.gdb: QProcess | None = None
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

    def closeEvent(self, event: PySide6.QtGui.QCloseEvent) -> None:
        """Called when window is closed. Cleanup all ptys and terminate the gdb process"""
        map(close_pty_pair, self.ttys.values())
        if self.gdb:
            logger.info("Closing GDB process")
            self.gdb.kill()
            self.gdb.waitForFinished()


    @Slot()
    def file_button_clicked(self):
        dialog = QFileDialog(self)
        dialog.setFileMode(QFileDialog.ExistingFile)
        dialog.setViewMode(QFileDialog.Detail)
        if dialog.exec() and len(dialog.selectedFiles()) > 0:
            file_name = dialog.selectedFiles()[0]
            self.start_gdb(file_name)


def run_gui(ttys: Dict[str, Tuple[int, int]]):
    app = QApplication(sys.argv)
    widget = PwnDbgGui(ttys)
    widget.show()
    sys.exit(app.exec())
