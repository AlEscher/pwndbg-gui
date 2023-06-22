# This Python file uses the following encoding: utf-8
import logging
import sys
from pathlib import Path
from typing import List

import PySide6
from PySide6.QtCore import Slot
from PySide6.QtGui import QTextOption, QTextCursor, QAction
from PySide6.QtWidgets import QApplication, QWidget, QFileDialog, QTextBrowser, QTextEdit, QMainWindow, QInputDialog, \
    QLineEdit

from context_window import ContextWindow
from main_text_edit import MainTextEdit
from pipe_util import delete_pipe, create_pipes
# Important:
# You need to run the following command to generate the ui_form.py file
#     pyside6-uic form.ui -o ui_form.py, or
#     pyside2-uic form.ui -o ui_form.py
from ui_form import Ui_PwnDbgGui

logger = logging.getLogger(__file__)


class PwnDbgGui(QMainWindow):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.menu_bar = None
        self.gdbinit = Path.home() / ".gdbinit"
        self.gdbinit_backup = self.gdbinit.read_bytes()
        logger.info("Creating pipes")
        self.pipes = create_pipes(["stack"])
        self.ui = Ui_PwnDbgGui()
        self.ui.setupUi(self)
        self.seg_to_widget = dict(stack=self.ui.stack)
        self.setup_menu()

    def setup_menu(self):
        self.menu_bar = self.menuBar()
        debug_menu = self.menu_bar.addMenu("&Debug")
        debug_toolbar = self.addToolBar("Debug")

        start_action = QAction("Start Program", self)
        start_action.setToolTip("Start the program to debug")
        start_action.triggered.connect(self.select_file)
        debug_menu.addAction(start_action)
        debug_toolbar.addAction(start_action)

        attach_name_action = QAction("Attach Via Name", self)
        attach_name_action.setToolTip("Attach to a running program via its name (must be unique)")
        attach_name_action.triggered.connect(self.query_process_name)
        debug_menu.addAction(attach_name_action)
        debug_toolbar.addAction(attach_name_action)

        attach_pid_action = QAction("Attach Via PID", self)
        attach_pid_action.setToolTip("Attach to a running program via its pid")
        attach_pid_action.triggered.connect(self.query_process_pid)
        debug_menu.addAction(attach_pid_action)
        debug_toolbar.addAction(attach_pid_action)

    def start_gdb(self, args: List[str]):
        """Runs gdb with the given program and waits for gdb to have started"""
        # Replace the "Main" widget with our custom implementation
        main_text_edit = MainTextEdit(parent=self, args=args)
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
    def select_file(self):
        dialog = QFileDialog(self)
        dialog.setFileMode(QFileDialog.FileMode.ExistingFile)
        dialog.setViewMode(QFileDialog.ViewMode.Detail)
        if dialog.exec() and len(dialog.selectedFiles()) > 0:
            file_name = dialog.selectedFiles()[0]
            self.start_gdb([file_name])

    @Slot()
    def query_process_name(self):
        name, ok = QInputDialog.getText(self, "Enter a running process name", "Name:", QLineEdit.EchoMode.Normal, "vuln")
        if ok and name:
            args = ["-p", f"$(pidof {name})"]
            self.start_gdb(args)

    def query_process_pid(self):
        pid, ok = QInputDialog.getInt(self, "Enter a running process pid", "PID:", minValue=0)
        if ok and pid > 0:
            args = ["-p", str(pid)]
            self.start_gdb(args)

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
