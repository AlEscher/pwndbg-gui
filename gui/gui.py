# This Python file uses the following encoding: utf-8
import logging
import sys
from typing import List

import PySide6
from PySide6.QtCore import Slot, Qt, Signal, QThread
from PySide6.QtGui import QTextOption, QAction, QKeySequence, QFont
from PySide6.QtWidgets import QApplication, QFileDialog, QMainWindow, QInputDialog, \
    QLineEdit, QMessageBox, QGroupBox, QVBoxLayout, QWidget, QSplitter, QHBoxLayout, QSpinBox, QLabel

from gui.constants import PwndbgGuiConstants
from gui.custom_widgets.context_list_widget import ContextListWidget
from gui.custom_widgets.context_text_edit import ContextTextEdit
from gui.gdb_handler import GdbHandler
from gui.html_style_delegate import HTMLDelegate
from gui.custom_widgets.main_context_widget import MainContextWidget
from gui.parser import ContextParser
# Important:
# You need to run the following command to generate the ui_form.py file
#     pyside6-uic form.ui -o ui_form.py, or
#     pyside2-uic form.ui -o ui_form.py
from gui.ui_form import Ui_PwnDbgGui

logger = logging.getLogger(__file__)


class PwnDbgGui(QMainWindow):
    change_gdb_setting = Signal(list)
    stop_gdb_thread = Signal()
    set_gdb_target_signal = Signal(list)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.main_text_edit: MainContextWidget | None = None
        self.gdb_thread = None
        self.gdb_handler = GdbHandler()
        self.stack_lines_incrementor: QSpinBox | None = None
        self.menu_bar = None
        self.ui = Ui_PwnDbgGui()
        self.ui.setupUi(self)
        # Make all widgets resizable with the window
        self.setCentralWidget(self.ui.top_splitter)
        self.setup_custom_widgets()
        self.seg_to_widget = dict(stack=self.ui.stack, code=self.ui.code, disasm=self.ui.disasm,
                                  backtrace=self.ui.backtrace, regs=self.ui.regs, ipython=self.ui.ipython,
                                  main=self.main_text_edit.output_widget)
        self.parser = ContextParser()
        self.init_gdb_handler()
        self.setup_menu()

    def setup_custom_widgets(self):
        """Ugly workaround to allow to use custom widgets.
            Using custom widgets in Qt Designer seems to only work for C++"""
        # Widget index depends on the order they were added in ui_form.py
        logger.debug("Replacing widgets with custom implementations")
        self.ui.stack = ContextListWidget(self)
        self.ui.stack.setObjectName("stack")
        self.ui.stack.setItemDelegate(HTMLDelegate())
        self.setup_context_pane(self.ui.stack, title="Stack", splitter=self.ui.splitter_4, index=2)
        self.ui.regs = ContextListWidget(self)
        self.ui.regs.setObjectName("regs")
        self.ui.regs.setItemDelegate(HTMLDelegate())
        self.setup_context_pane(self.ui.regs, title="Registers", splitter=self.ui.splitter_3, index=0)
        self.ui.backtrace = ContextTextEdit(self)
        self.ui.backtrace.setObjectName("backtrace")
        self.setup_context_pane(self.ui.backtrace, title="Backtrace", splitter=self.ui.splitter_3, index=1)
        self.ui.disasm = ContextTextEdit(self)
        self.ui.disasm.setObjectName("disasm")
        self.setup_context_pane(self.ui.disasm, title="Disassembly", splitter=self.ui.code_splitter, index=0)
        self.ui.code = ContextTextEdit(self)
        self.ui.code.setObjectName("code")
        self.setup_context_pane(self.ui.code, title="Code", splitter=self.ui.code_splitter, index=1)
        self.main_text_edit = MainContextWidget(parent=self)
        self.ui.splitter.replaceWidget(0, self.main_text_edit)
        # https://stackoverflow.com/a/66067630
        self.main_text_edit.show()

    def setup_context_pane(self, context_widget: QWidget, title: str, splitter: QSplitter, index: int):
        """Sets up the layout for a context pane"""
        # GroupBox needs to have parent before being added to splitter (see SO below)
        context_box = QGroupBox(title, self)
        context_box.setAlignment(Qt.AlignmentFlag.AlignCenter)
        context_box.setFlat(True)
        context_layout = QVBoxLayout()
        if context_widget == self.ui.stack:
            self.add_stack_header(context_layout)
        context_layout.addWidget(context_widget)
        context_box.setLayout(context_layout)
        splitter.replaceWidget(index, context_box)
        # https://stackoverflow.com/a/66067630
        context_box.show()

    def setup_menu(self):
        self.menu_bar = self.menuBar()
        debug_menu = self.menu_bar.addMenu("&Debug")
        debug_toolbar = self.addToolBar("Debug")

        start_action = QAction("Start Program", self)
        start_action.setStatusTip("Start the program to debug")
        start_action.triggered.connect(self.select_file)
        debug_menu.addAction(start_action)
        debug_toolbar.addAction(start_action)

        attach_name_action = QAction("Attach Via Name", self)
        attach_name_action.setStatusTip("Attach to a running program via its name (must be unique)")
        attach_name_action.triggered.connect(self.query_process_name)
        debug_menu.addAction(attach_name_action)
        debug_toolbar.addAction(attach_name_action)

        attach_pid_action = QAction("Attach Via PID", self)
        attach_pid_action.setStatusTip("Attach to a running program via its pid")
        attach_pid_action.triggered.connect(self.query_process_pid)
        debug_menu.addAction(attach_pid_action)
        debug_toolbar.addAction(attach_pid_action)

        debug_menu.addSeparator()
        exit_action = QAction("E&xit", self)
        exit_action.setShortcut(QKeySequence.StandardKey.Quit)
        exit_action.setStatusTip("Exit the application")
        exit_action.triggered.connect(self.close)
        debug_menu.addAction(exit_action)

        about_menu = self.menu_bar.addMenu("About")
        about_action = QAction("About", self)
        about_action.triggered.connect(self.about)
        about_menu.addAction(about_action)
        about_qt_action = QAction("About Qt", self)
        about_qt_action.triggered.connect(QApplication.aboutQt)
        about_menu.addAction(about_qt_action)

    def init_gdb_handler(self):
        self.gdb_thread = QThread()
        self.gdb_handler.moveToThread(self.gdb_thread)
        self.set_gdb_target_signal.connect(self.gdb_handler.set_target)
        self.stack_lines_incrementor.valueChanged.connect(self.gdb_handler.update_stack_lines)
        # Allow the worker to update contexts in the GUI thread
        self.gdb_handler.update_gui.connect(self.update_pane)
        # Thread cleanup
        self.gdb_thread.finished.connect(self.gdb_handler.deleteLater)
        self.stop_gdb_thread.connect(self.gdb_thread.quit)
        logger.debug("Starting new worker threads")
        self.gdb_thread.start()

    def closeEvent(self, event: PySide6.QtGui.QCloseEvent) -> None:
        """Called when window is closed. Stop our worker thread"""
        logger.debug("Stopping GDB handler update thread")
        self.stop_gdb_thread.emit()

    def add_stack_header(self, layout: QVBoxLayout):
        # Add a stack count inc-/decrementor
        header_layout = QHBoxLayout()
        header_layout.setAlignment(Qt.AlignmentFlag.AlignLeft)
        stack_lines_label = QLabel("Stack Lines:")
        header_layout.addWidget(stack_lines_label)
        self.stack_lines_incrementor = QSpinBox()
        self.stack_lines_incrementor.setRange(1, 999)
        self.stack_lines_incrementor.setValue(8)  # Maybe retrieve the set value from gdb?
        header_layout.addWidget(self.stack_lines_incrementor)
        layout.addLayout(header_layout)

    @Slot()
    def select_file(self):
        dialog = QFileDialog(self)
        dialog.setFileMode(QFileDialog.FileMode.ExistingFile)
        dialog.setViewMode(QFileDialog.ViewMode.Detail)
        if dialog.exec() and len(dialog.selectedFiles()) > 0:
            file_name = dialog.selectedFiles()[0]
            self.set_gdb_target_signal.emit(["file", file_name])

    @Slot()
    def query_process_name(self):
        name, ok = QInputDialog.getText(self, "Enter a running process name", "Name:", QLineEdit.EchoMode.Normal,
                                        "vuln")
        if ok and name:
            args = ["attach", f"$(pidof {name})"]
            self.set_gdb_target_signal.emit(args)

    def query_process_pid(self):
        pid, ok = QInputDialog.getInt(self, "Enter a running process pid", "PID:", minValue=0)
        if ok and pid > 0:
            args = ["attach", str(pid)]
            self.set_gdb_target_signal.emit(args)

    @Slot(str, bytes)
    def update_pane(self, context: str, content: bytes):
        widget: ContextTextEdit | ContextListWidget = self.seg_to_widget[context]
        logger.debug("Updating context %s", widget.objectName())
        html = self.parser.to_html(content)
        widget.add_content(html)

    @Slot()
    def about(self):
        QMessageBox.about(self, "About PwndbgGui", "The <b>Application</b> example demonstrates how to "
                                                   "write modern GUI applications using Qt, with a menu bar, "
                                                   "toolbars, and a status bar.")


def run_gui():
    # Set font where characters are all equally wide (monospace) to help with formatting and alignment
    font = QFont(PwndbgGuiConstants.FONT)
    font.setStyleHint(QFont.StyleHint.Monospace)
    QApplication.setFont(font)
    app = QApplication(sys.argv)
    window = PwnDbgGui()
    window.show()
    sys.exit(app.exec())
