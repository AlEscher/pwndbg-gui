# This Python file uses the following encoding: utf-8
import logging
import sys
from pathlib import Path

import PySide6
from PySide6.QtCore import Slot
from PySide6.QtGui import QTextOption, QTextCursor, QAction
from PySide6.QtWidgets import QApplication, QWidget, QFileDialog, QTextBrowser, QTextEdit, QMainWindow

from context_window import ContextWindow
from main_text_edit import MainTextEdit
from pty_util import delete_pipe, create_pipes
# Important:
# You need to run the following command to generate the ui_form.py file
#     pyside6-uic form.ui -o ui_form.py, or
#     pyside2-uic form.ui -o ui_form.py
from ui_form import Ui_PwnDbgGui

logger = logging.getLogger(__file__)


class PwnDbgGui(QMainWindow):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.gdbinit = Path.home() / ".gdbinit"
        self.gdbinit_backup = self.gdbinit.read_bytes()
        logger.info("Creating pipes")
        self.pipes = create_pipes([])
        self.ui = Ui_PwnDbgGui()
        self.ui.setupUi(self)
        self.seg_to_widget = dict(stack=self.ui.stack)
        self.setup_menu()

    def setup_menu(self):
        menu_bar = self.menuBar()
        debug_menu = menu_bar.addMenu("&Debug")
        debug_toolbar = self.addToolBar("Debug")
        start_action = QAction("Start Program", self)
        start_action.setToolTip("Start the program to debug")
        start_action.triggered.connect(self.file_button_clicked)
        debug_menu.addAction(start_action)
        debug_toolbar.addAction(start_action)

    def start_gdb(self, debugee: str):
        """Runs gdb with the given program and waits for gdb to have started"""
        # Replace the "Main" widget with our custom implementation
        main_text_edit = MainTextEdit(parent=self, debugee=debugee)
        self.ui.splitter.replaceWidget(0, main_text_edit)
        self.seg_to_widget["main"] = main_text_edit
        self.seg_to_widget["main"].gdb_read.emit()

    def closeEvent(self, event: PySide6.QtGui.QCloseEvent) -> None:
        """Called when window is closed. Cleanup all ptys and terminate the gdb process"""
        logger.debug("Resetting gdbinit")
        self.gdbinit.write_bytes(self.gdbinit_backup)
        for pipe in self.pipes.values():
            delete_pipe(pipe)
        logger.debug("Stopping MainTextEdit update thread")
        self.seg_to_widget["main"].gdb_stop.emit()
        self.seg_to_widget["main"].stop_thread.emit()

    @Slot()
    def file_button_clicked(self):
        dialog = QFileDialog(self)
        dialog.setFileMode(QFileDialog.FileMode.ExistingFile)
        dialog.setViewMode(QFileDialog.ViewMode.Detail)
        if dialog.exec() and len(dialog.selectedFiles()) > 0:
            file_name = dialog.selectedFiles()[0]
            self.start_gdb(file_name)

    @Slot(str, str)
    def update_pane(self, context: str, content: bytes):
        widget: QTextEdit | QTextBrowser | ContextWindow = self.seg_to_widget[context]
        logger.debug("Updating context %s with \"%s...\"", widget.objectName(), content[:100])
        widget.add_gdb_output(content)
        cursor = widget.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.End, QTextCursor.MoveMode.MoveAnchor)
        widget.setTextCursor(cursor)


def run_gui():
    app = QApplication(sys.argv)
    window = PwnDbgGui()
    window.show()
    sys.exit(app.exec())
