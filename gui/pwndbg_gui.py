import logging
import sys
from pathlib import Path
from typing import List
from os import path

sys.path.extend([path.join(path.dirname(__file__), path.pardir)])
from gui.custom_widgets.backtrace_context_widget import BacktraceContextWidget
from gui.custom_widgets.code_context_widget import CodeContextWidget
from gui.custom_widgets.disasm_context_widget import DisasmContextWidget
from gui.custom_widgets.info_message_box import InfoMessageBox
from gui.custom_widgets.register_context_widget import RegisterContextWidget
from gui.custom_widgets.stack_context_widget import StackContextWidget

import PySide6
from PySide6.QtCore import Slot, Qt, Signal, QThread, QSettings, QByteArray
from PySide6.QtGui import QTextOption, QAction, QKeySequence, QFont, QPalette, QColor
from PySide6.QtWidgets import QApplication, QFileDialog, QMainWindow, QInputDialog, \
    QLineEdit, QMessageBox, QSpinBox, QSplitter

from gui.constants import PwndbgGuiConstants
from gui.custom_widgets.context_list_widget import ContextListWidget
from gui.custom_widgets.context_text_edit import ContextTextEdit
from gui.custom_widgets.main_context_widget import MainContextWidget
from gui.gdb_handler import GdbHandler
from gui.custom_widgets.heap_context_widget import HeapContextWidget
from gui.custom_widgets.watches_context_widget import HDumpContextWidget
from gui.gdb_reader import GdbReader
from gui.inferior_handler import InferiorHandler
from gui.parser import ContextParser
# Important:
# You need to run the following command to generate the ui_form.py file
#     pyside6-uic form.ui -o ui_form.py, or
#     pyside2-uic form.ui -o ui_form.py
from gui.ui_form import Ui_PwnDbgGui

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s | [%(levelname)s] : %(message)s')
logger = logging.getLogger(__file__)


class PwnDbgGui(QMainWindow):
    change_gdb_setting = Signal(list)
    stop_gdb_threads = Signal()
    set_gdb_file_target_signal = Signal(list)
    set_gdb_pid_target_signal = Signal(list)
    set_gdb_source_dir_signal = Signal(list)
    set_gdb_tty = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        # An overview of all pwndbg commands
        self.pwndbg_cmds = ""
        self.main_context: MainContextWidget | None = None
        # Thread that will handle all writing to GDB
        self.gdb_handler_thread: QThread | None = None
        # Thread that will continuously read from GDB
        self.gdb_reader_thread: QThread | None = None
        # Thread that will continuously read and write to inferior
        self.inferior_thread: QThread | None = None
        self.gdb_handler = GdbHandler()
        self.gdb_reader = GdbReader(self.gdb_handler.controller)
        self.inferior_handler = InferiorHandler()
        self.stack_lines_incrementor: QSpinBox | None = None
        self.menu_bar = None
        self.ui = Ui_PwnDbgGui()
        self.ui.setupUi(self)
        # Make all widgets resizable with the window
        self.setCentralWidget(self.ui.top_splitter)
        self.setup_custom_widgets()
        self.seg_to_widget = dict(stack=self.ui.stack, code=self.ui.code, disasm=self.ui.disasm,
                                  backtrace=self.ui.backtrace, regs=self.ui.regs,
                                  main=self.main_context.output_widget)
        self.parser = ContextParser()
        self.setup_gdb_workers()
        self.setup_menu()
        self.gdb_handler.init()
        self.setup_inferior()
        self.load_state()

    def setup_custom_widgets(self):
        """Ugly workaround to allow to use custom widgets.
            Using custom widgets in Qt Designer seems to only work for C++"""
        logger.debug("Replacing widgets with custom implementations")
        # Widget index depends on the order they were added in ui_form.py
        self.ui.stack = StackContextWidget(self, title="Stack", splitter=self.ui.splitter_4, index=2)
        self.ui.regs = RegisterContextWidget(self, title="Registers", splitter=self.ui.splitter_3, index=0)
        self.ui.backtrace = BacktraceContextWidget(self, title="Backtrace", splitter=self.ui.splitter_3, index=1)
        self.ui.disasm = DisasmContextWidget(self, title="Disassembly", splitter=self.ui.code_splitter, index=0)
        self.ui.code = CodeContextWidget(self, title="Code", splitter=self.ui.code_splitter, index=1)
        self.ui.heap = HeapContextWidget(self)
        self.ui.watches = HDumpContextWidget(self)
        self.main_context = MainContextWidget(parent=self)
        self.ui.splitter.replaceWidget(0, self.main_context)

    def setup_menu(self):
        """Create the menu and toolbar at the top of the window"""
        self.menu_bar = self.menuBar()
        debug_menu = self.menu_bar.addMenu("&Debug")
        debug_toolbar = self.addToolBar("Debug")
        debug_toolbar.setObjectName("debugToolbar")

        start_action = QAction("Start Program", self)
        start_action.setToolTip("Start the program to debug")
        start_action.setShortcut(QKeySequence.StandardKey.New)
        start_action.triggered.connect(self.select_file)
        debug_menu.addAction(start_action)
        debug_toolbar.addAction(start_action)

        attach_name_action = QAction("Attach Via Name", self)
        attach_name_action.setToolTip("Attach to a running program via its name (requires sudo)")
        attach_name_action.triggered.connect(self.query_process_name)
        debug_menu.addAction(attach_name_action)
        debug_toolbar.addAction(attach_name_action)

        attach_pid_action = QAction("Attach Via PID", self)
        attach_pid_action.setToolTip("Attach to a running program via its pid (requires sudo)")
        attach_pid_action.triggered.connect(self.query_process_pid)
        debug_menu.addAction(attach_pid_action)
        debug_toolbar.addAction(attach_pid_action)

        debug_menu.addSeparator()
        exit_action = QAction("E&xit", self)
        exit_action.setShortcut(QKeySequence.StandardKey.Quit)
        exit_action.setToolTip("Exit the application")
        exit_action.triggered.connect(self.close)
        debug_menu.addAction(exit_action)

        about_menu = self.menu_bar.addMenu("About")
        about_action = QAction("About", self)
        about_action.triggered.connect(self.about)
        about_menu.addAction(about_action)
        about_pwndbg_action = QAction("About Pwndbg", self)
        about_pwndbg_action.triggered.connect(self.about_pwndbg)
        about_menu.addAction(about_pwndbg_action)
        about_qt_action = QAction("About Qt", self)
        about_qt_action.triggered.connect(QApplication.aboutQt)
        about_menu.addAction(about_qt_action)

    def setup_gdb_workers(self):
        """Setup our worker threads and connect all required signals with their slots"""
        self.gdb_handler_thread = QThread()
        self.gdb_reader_thread = QThread()
        self.gdb_handler.moveToThread(self.gdb_handler_thread)
        self.gdb_reader.moveToThread(self.gdb_reader_thread)
        # Allow widgets to send signals that interact with GDB
        self.set_gdb_file_target_signal.connect(self.gdb_handler.set_file_target)
        self.set_gdb_pid_target_signal.connect(self.gdb_handler.set_pid_target)
        self.set_gdb_source_dir_signal.connect(self.gdb_handler.set_source_dir)
        self.set_gdb_tty.connect(self.gdb_handler.set_tty)
        self.ui.stack.stack_lines_incrementor.valueChanged.connect(self.gdb_handler.update_stack_lines)
        self.ui.stack.execute_xinfo.connect(self.gdb_handler.execute_xinfo)
        self.ui.regs.execute_xinfo.connect(self.gdb_handler.execute_xinfo)
        # Allow the worker to update contexts in the GUI thread
        self.gdb_handler.update_gui.connect(self.update_pane)
        self.gdb_reader.update_gui.connect(self.update_pane)
        self.gdb_reader.inferior_state_changed.connect(self.main_context.change_input_label)
        self.gdb_reader.send_pwndbg_about.connect(self.receive_pwndbg_about)
        self.gdb_reader.send_xinfo.connect(self.display_xinfo_result)
        # Allow the heap context to receive the results it requests
        self.gdb_reader.send_heap_try_free_response.connect(self.ui.heap.receive_try_free_result)
        self.gdb_reader.send_heap_heap_response.connect(self.ui.heap.receive_heap_result)
        self.gdb_reader.send_heap_bins_response.connect(self.ui.heap.receive_bins_result)
        # Allow the watches context to receive the hexdump results
        self.gdb_reader.send_watches_hexdump_response.connect(self.ui.watches.receive_hexdump_result)
        # Allow the "regs" context to receive information about the fs register
        self.gdb_reader.send_fs_base_response.connect(self.ui.regs.receive_fs_base)
        # Thread cleanup
        self.gdb_handler_thread.finished.connect(self.gdb_handler.deleteLater)
        self.gdb_reader_thread.finished.connect(self.gdb_reader.deleteLater)
        self.stop_gdb_threads.connect(lambda: self.gdb_reader.set_run(False))
        self.stop_gdb_threads.connect(self.gdb_handler_thread.quit)
        self.stop_gdb_threads.connect(self.gdb_reader_thread.quit)
        logger.debug("Starting new worker threads")
        self.gdb_reader_thread.started.connect(self.gdb_reader.read_with_timeout)
        self.gdb_handler_thread.start()
        self.gdb_reader_thread.start()
        logger.info("Started worker threads")

    def setup_inferior(self):
        # Thread setup
        self.inferior_thread = QThread()
        self.inferior_handler.moveToThread(self.inferior_thread)
        # Connect signals from inferior_handler
        self.inferior_handler.update_gui.connect(self.update_pane)
        # execute gdb command to redirect inferior to tty
        self.set_gdb_tty.emit(self.inferior_handler.tty)
        # Thread cleanup
        self.inferior_thread.finished.connect(self.inferior_handler.deleteLater())
        self.stop_gdb_threads.connect(lambda: self.inferior_handler.set_run(False))
        self.stop_gdb_threads.connect(self.inferior_thread.quit)
        # Thread start
        self.inferior_thread.started.connect(self.inferior_handler.inferior_runs)
        self.inferior_thread.start()

    def closeEvent(self, event: PySide6.QtGui.QCloseEvent) -> None:
        """Called when window is closed. Stop our worker threads"""
        logger.debug("Stopping GDB threads")
        self.stop_gdb_threads.emit()
        self.save_state()
        logger.debug("Waiting for GDB Handler thread")
        self.gdb_handler_thread.wait()
        logger.debug("Waiting for GDB Reader thread")
        self.gdb_reader_thread.wait()
        logger.debug("Waiting for Inferior thread")
        self.inferior_thread.wait()
        event.accept()

    @Slot()
    def select_file(self):
        """Query the user for the path to an executable with a file dialog in order to start it"""
        dialog = QFileDialog(self)
        dialog.setFileMode(QFileDialog.FileMode.ExistingFile)
        dialog.setViewMode(QFileDialog.ViewMode.Detail)
        if dialog.exec() and len(dialog.selectedFiles()) > 0:
            file_name = dialog.selectedFiles()[0]
            self.set_gdb_file_target_signal.emit([file_name])
            # GDB only looks for source files in the cwd, so we additionally add the directory of the executable
            self.set_gdb_source_dir_signal.emit([str(Path(file_name).parent)])

    @Slot()
    def query_process_name(self):
        """Query the user for a process name in order to attach to it"""
        name, ok = QInputDialog.getText(self, "Enter a running process name", "Name:", QLineEdit.EchoMode.Normal,
                                        "vuln")
        if ok and name:
            args = [f"$(pidof {name})"]
            self.set_gdb_pid_target_signal.emit(args)

    def query_process_pid(self):
        """Query the user for process ID in order to attach to it"""
        pid, ok = QInputDialog.getInt(self, "Enter a running process pid", "PID:", minValue=0)
        if ok and pid > 0:
            args = [str(pid)]
            self.set_gdb_pid_target_signal.emit(args)

    @Slot(str, bytes)
    def update_pane(self, context: str, content: bytes):
        """Used by other threads to update widgets in the GUI. Updates to the GUI have to be made in the GUI's thread"""
        widget: ContextTextEdit | ContextListWidget = self.seg_to_widget[context]
        logger.debug("Updating context %s", widget.objectName())
        remove_header = True
        if context == "main":
            remove_header = False
            # Main should end with newline
            if content != b"" and not content.endswith(b"\n"):
                content += b"\n"
        html = self.parser.to_html(content, remove_header)
        widget.add_content(html)

    @Slot()
    def about(self):
        """Display the About section for our GUI"""
        QMessageBox.about(self, "About PwndbgGui", PwndbgGuiConstants.ABOUT_TEXT)

    @Slot(bytes)
    def receive_pwndbg_about(self, content: bytes):
        """Receive the output of the command overview for pwndbg"""
        self.pwndbg_cmds = self.parser.to_html(content)

    @Slot()
    def about_pwndbg(self):
        """Display the About section for pwndbg"""
        popup = InfoMessageBox(self, "About Pwndbg", self.pwndbg_cmds, "https://github.com/pwndbg/pwndbg#pwndbg")
        popup.exec()

    @Slot(bytes)
    def display_xinfo_result(self, content: bytes):
        message = self.parser.to_html(content)
        # pwndbg doesn't seem to have documentation on commands, so we link to code ¯\_(ツ)_/¯
        popup = InfoMessageBox(self, "xinfo", message, "https://github.com/pwndbg/pwndbg/blob/dev/pwndbg/commands"
                                                       "/xinfo.py#L102")
        popup.show()

    def save_state(self):
        """Save the state of the current session (e.g. in ~/.config folder on Linux)"""
        settings = QSettings(PwndbgGuiConstants.SETTINGS_FOLDER, PwndbgGuiConstants.SETTINGS_FILE)
        logger.info("Saving GUI layout state to %s", settings.fileName())
        settings.setValue(PwndbgGuiConstants.SETTINGS_WINDOW_STATE, self.saveState())
        settings.setValue(PwndbgGuiConstants.SETTINGS_WINDOW_GEOMETRY, self.saveGeometry())
        settings = QSettings(PwndbgGuiConstants.SETTINGS_FOLDER, PwndbgGuiConstants.SETTINGS_FILE)
        splitters = self.findChildren(QSplitter)
        splitter_sizes: List[QByteArray] = [splitter.saveGeometry() for splitter in splitters]
        splitter_states: List[QByteArray] = [splitter.saveState() for splitter in splitters]
        settings.setValue(PwndbgGuiConstants.SPLITTER_GEOMETRIES, b','.join(map(QByteArray.toBase64, splitter_sizes)))
        settings.setValue(PwndbgGuiConstants.SPLITTER_STATES, b','.join(map(QByteArray.toBase64, splitter_states)))

    def load_state(self):
        """Load the state of the previous session"""
        settings = QSettings(PwndbgGuiConstants.SETTINGS_FOLDER, PwndbgGuiConstants.SETTINGS_FILE)
        state = settings.value(PwndbgGuiConstants.SETTINGS_WINDOW_STATE)
        if state:
            self.restoreState(state)
        geometry = settings.value(PwndbgGuiConstants.SETTINGS_WINDOW_GEOMETRY)
        if geometry:
            self.restoreGeometry(geometry)
        splitter_sizes = settings.value(PwndbgGuiConstants.SPLITTER_GEOMETRIES)
        splitter_states = settings.value(PwndbgGuiConstants.SPLITTER_STATES)
        if splitter_sizes is not None and splitter_states is not None:
            logger.info("Loading existing GUI layout state from %s", settings.fileName())
            splitter_sizes = [QByteArray.fromBase64(size) for size in splitter_sizes.split(b',')]
            splitter_states = [QByteArray.fromBase64(size) for size in splitter_states.split(b',')]
            splitters = self.findChildren(QSplitter)
            for splitter, size, state in zip(splitters, splitter_sizes, splitter_states):
                splitter.restoreGeometry(size)
                splitter.restoreState(state)


def run_gui():
    """Start our GUI with the specified font and theme"""
    # Set font where characters are all equally wide (monospace) to help with formatting and alignment
    font = QFont(PwndbgGuiConstants.FONT)
    font.setStyleHint(QFont.StyleHint.Monospace)
    QApplication.setFont(font)
    app = QApplication(sys.argv)

    app.setStyle("Fusion")
    # Create a dark palette: https://stackoverflow.com/a/45634644 (Change: Fix tooltip color)
    dark_palette = QPalette()
    dark_palette.setColor(QPalette.ColorRole.Window, QColor(53, 53, 53))
    dark_palette.setColor(QPalette.ColorRole.WindowText, Qt.GlobalColor.white)
    dark_palette.setColor(QPalette.ColorGroup.Disabled, QPalette.ColorRole.WindowText, QColor(127, 127, 127))
    dark_palette.setColor(QPalette.ColorRole.Base, QColor(42, 42, 42))
    dark_palette.setColor(QPalette.ColorRole.AlternateBase, QColor(66, 66, 66))
    dark_palette.setColor(QPalette.ColorRole.ToolTipBase, Qt.GlobalColor.black)
    dark_palette.setColor(QPalette.ColorRole.ToolTipText, Qt.GlobalColor.white)
    dark_palette.setColor(QPalette.ColorRole.Text, Qt.GlobalColor.white)
    dark_palette.setColor(QPalette.ColorGroup.Disabled, QPalette.ColorRole.Text, QColor(127, 127, 127))
    dark_palette.setColor(QPalette.ColorRole.Dark, QColor(35, 35, 35))
    dark_palette.setColor(QPalette.ColorRole.Shadow, QColor(20, 20, 20))
    dark_palette.setColor(QPalette.ColorRole.Button, QColor(53, 53, 53))
    dark_palette.setColor(QPalette.ColorRole.ButtonText, Qt.GlobalColor.white)
    dark_palette.setColor(QPalette.ColorGroup.Disabled, QPalette.ColorRole.ButtonText, QColor(127, 127, 127))
    dark_palette.setColor(QPalette.ColorRole.BrightText, Qt.GlobalColor.red)
    dark_palette.setColor(QPalette.ColorRole.Link, QColor(42, 130, 218))
    dark_palette.setColor(QPalette.ColorRole.Highlight, QColor(42, 130, 218))
    dark_palette.setColor(QPalette.ColorGroup.Disabled, QPalette.ColorRole.Highlight, QColor(80, 80, 80))
    dark_palette.setColor(QPalette.ColorRole.HighlightedText, Qt.GlobalColor.white)
    dark_palette.setColor(QPalette.ColorGroup.Disabled, QPalette.ColorRole.HighlightedText, QColor(127, 127, 127))
    # Set the dark palette
    app.setPalette(dark_palette)
    # fix for Tooltip colors
    app.setStyleSheet("""
        QToolTip {
            background-color: #303030;
            color: white;
        }
    """)

    window = PwnDbgGui()
    window.showMaximized()
    sys.exit(app.exec())


def main():
    logger.info("Starting GUI")
    run_gui()


if __name__ == "__main__":
    main()
