import ast
import logging
import re
from typing import TYPE_CHECKING, List

from PySide6.QtCore import Qt, Signal, Slot, QEvent
from PySide6.QtGui import QIcon, QTextCursor
from PySide6.QtWidgets import QGroupBox, QVBoxLayout, QLineEdit, QHBoxLayout, QPushButton, QLabel, QWidget, QComboBox, \
    QFrame
from gui.constants import PwndbgGuiConstants
from gui.custom_widgets.context_text_edit import ContextTextEdit
from gui.inferior_handler import InferiorHandler
from gui.inferior_state import InferiorState

# Prevent circular import error
if TYPE_CHECKING:
    from gui.pwndbg_gui import PwnDbgGui

logger = logging.getLogger(__file__)


class MainContextOutput(ContextTextEdit):
    def __init__(self, parent: QWidget):
        super().__init__(parent)
        self.setObjectName("main")

    def add_content(self, content: str):
        """Appends content instead of replacing it like other normal ContextTextEdit widgets"""
        # Prevent selected text from being overwritten
        cursor = self.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.End, QTextCursor.MoveMode.MoveAnchor)
        self.setTextCursor(cursor)
        self.insertHtml(content)
        # Scroll to the bottom
        self.ensureCursorVisible()


class MainContextWidget(QGroupBox):
    """The main context widget with which the user can interact with GDB and receive data"""
    # Signal to send a command to GDB MI
    gdb_write = Signal(str)
    # Signal to send inferior input via GDB
    gdb_write_input = Signal(bytes)
    # Signal to send inferior input via InferiorHandler's TTY
    inferior_write = Signal(bytes)
    # Signal to update data in the GUI
    update_gui = Signal(str, bytes)
    # Send a search request to GDB
    gdb_search = Signal(list)

    def __init__(self, parent: 'PwnDbgGui'):
        super().__init__(parent)
        self.update_gui.connect(parent.update_pane)
        self.buttons_data = {'s&tart': (self.start, "media-record"), '&r': (self.run, "media-playback-start"), '&c': (self.continue_execution, "media-skip-forward"), '&n': (self.next, "media-seek-forward"),
                             '&s': (self.step, "go-bottom"), 'ni': (self.next_instruction, "go-next"), 'si': (self.step_into, "go-down")}
        # Whether the inferior was attached or started by GDB. If attached, we cannot divert I/O of the inferior via
        # GDB to the tty, so we need to send input via the GdbHandler.
        self.inferior_attached = False
        self.setup_worker_signals(parent)
        self.input_label = QLabel(f"<span style=' color:{PwndbgGuiConstants.RED};'>pwndbg></span>")
        self.output_widget = MainContextOutput(self)
        self.input_widget = QLineEdit(self)
        self.search_input_widget = QLineEdit(self)
        self.search_input_widget.returnPressed.connect(self.handle_search_submit)
        self.search_input_widget.setPlaceholderText("Search data...")
        self.search_drop_down = QComboBox(self)
        self.search_drop_down.addItems(["byte", "word", "dword", "qword", "pointer", "string", "bytes"])
        self.search_drop_down.setCurrentText("bytes")
        self.search_drop_down.setToolTip("Select the type of data you want to search for")
        self.input_widget.returnPressed.connect(self.handle_submit)
        self.input_widget.installEventFilter(self)
        # The currently selected command in the command history, for when the user presses ↑ and ↓
        self.current_cmd_index = 0
        self.buttons = QHBoxLayout()
        self.setup_buttons()
        self.setup_widget_layout()
        self.command_history: List[str] = [""]

    def setup_widget_layout(self):
        """Create the layout of this widget and its sub widgets"""
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setFlat(True)
        context_layout = QVBoxLayout()
        # The layout containing the search field and buttons
        top_line_layout = QHBoxLayout()
        top_line_layout.addWidget(self.search_input_widget)
        top_line_layout.addWidget(self.search_drop_down)
        separator_line = QFrame(self)
        separator_line.setFrameShape(QFrame.Shape.VLine)
        separator_line.setFrameShadow(QFrame.Shadow.Sunken)
        top_line_layout.addWidget(separator_line)
        top_line_layout.addLayout(self.buttons)
        context_layout.addLayout(top_line_layout)
        context_layout.addWidget(self.output_widget)
        input_layout = QHBoxLayout()
        input_layout.addWidget(self.input_label)
        input_layout.addWidget(self.input_widget)
        context_layout.addLayout(input_layout)
        self.setLayout(context_layout)

    def setup_buttons(self):
        """Setup the convenience buttons (Run, Continue, Step, etc...)"""
        self.buttons.setAlignment(Qt.AlignmentFlag.AlignRight)
        for label, data in self.buttons_data.items():
            callback, icon = data
            button = QPushButton(label)
            button.clicked.connect(callback)
            if icon is not None:
                button.setIcon(QIcon.fromTheme(icon))
            if button.shortcut() is not None:
                button.setToolTip(button.shortcut().toString())
            self.buttons.addWidget(button)

    def setup_worker_signals(self, parent: 'PwnDbgGui'):
        """Connect signals to the GDB and Inferior writer to allow this widget to forward commands/input"""
        # Allow giving the thread work from outside
        self.gdb_write.connect(parent.gdb_handler.send_command)
        self.inferior_write.connect(parent.inferior_handler.inferior_write)

    @Slot()
    def handle_submit(self):
        """Callback for when the user presses Enter in the main widget's input field"""
        if InferiorHandler.INFERIOR_STATE == InferiorState.RUNNING:
            # Inferior is running, send to inferior
            self.submit_input()
        else:
            # Enter was pressed, send command to pwndbg
            self.submit_cmd()

    @Slot()
    def start(self):
        """Callback of the start button"""
        logger.debug("Executing start callback")
        self.gdb_write.emit("start")

    @Slot()
    def run(self):
        """Callback of the Run button"""
        logger.debug("Executing r callback")
        self.gdb_write.emit("r")

    @Slot()
    def continue_execution(self):
        """Callback of the Continue button"""
        logger.debug("Executing c callback")
        self.gdb_write.emit("c")

    @Slot()
    def next(self):
        """Callback of the Next button"""
        logger.debug("Executing n callback")
        self.gdb_write.emit("n")

    @Slot()
    def step(self):
        """Callback of the Step button"""
        logger.debug("Executing s callback")
        self.gdb_write.emit("s")

    @Slot()
    def next_instruction(self):
        """Callback of the Next Instruction button"""
        logger.debug("Executing ni callback")
        self.gdb_write.emit("ni")

    @Slot()
    def step_into(self):
        """Callback of the Step Instruction button"""
        logger.debug("Executing si callback")
        self.gdb_write.emit("si")

    @Slot(bool)
    def change_input_label(self, is_pwndbg: bool):
        """Update the input label's text"""
        if is_pwndbg:
            self.input_label.setText(f"<span style=' color:{PwndbgGuiConstants.RED};'>pwndbg></span>")
        else:
            self.input_label.setText(f"<span style=' color:{PwndbgGuiConstants.GREEN};'>target></span>")

    @Slot()
    def handle_search_submit(self):
        search_value = self.search_input_widget.text()
        value_type = self.search_drop_down.currentText()
        if value_type == "bytes":
            # Wrap the user input with "", otherwise characters like "'" and " " cause problems
            search_value = f'"{search_value}"'
        params = ["-t", value_type, search_value]
        logger.debug("Executing search with %s", params)
        self.gdb_search.emit(params)
        self.search_input_widget.clear()

    def submit_cmd(self):
        """Submit a command to GDB"""
        user_line = self.input_widget.text()
        if self.command_history[-1] != user_line:
            self.command_history.insert(-1, user_line)
            self.current_cmd_index = len(self.command_history) - 1
        logger.debug("Sending command '%s' to gdb", user_line)
        self.update_gui.emit("main", f"> {user_line}\n".encode())
        self.gdb_write.emit(user_line)
        self.input_widget.clear()

    def submit_input(self):
        """Submit an input to the inferior process"""
        user_line = self.input_widget.text()
        logger.debug("Sending input '%s' to inferior", user_line)
        user_input = b""
        # Check if the user wants to input a byte string literal, i.e. the input is in the form: 'b"MyInput \x12\x34"'
        if re.match(r'^b["\'].*["\']$', user_line):
            # Parse the str as if it were a bytes object
            # literal_eval is safer than eval(), however it still poses security risks regarding DoS, which we don't care about
            logger.debug("Trying to evaluate literal '%s'", user_line)
            byte_string = ast.literal_eval(user_line)
            logger.debug("Parsed input as bytes string, final input: %s", byte_string)
            # Don't pass a newline here, the user needs to specify this himself by writing '\n' at the end of his input
            user_input = byte_string
        else:
            user_input = user_line.encode() + b"\n"
        if self.inferior_attached:
            self.gdb_write_input.emit(user_input)
        else:
            self.inferior_write.emit(user_input)
        self.input_widget.clear()

    def eventFilter(self, source: QWidget, event: QEvent):
        """Callback for Qt events. Handles the navigation of the user's command history"""
        # https://stackoverflow.com/a/46506129
        if event.type() != QEvent.Type.KeyPress or source is not self.input_widget:
            return super().eventFilter(source, event)
        if event.key() == Qt.Key.Key_Down:
            self.current_cmd_index = min(len(self.command_history) - 1, self.current_cmd_index + 1)
            self.input_widget.setText(self.command_history[self.current_cmd_index])
        elif event.key() == Qt.Key.Key_Up:
            self.current_cmd_index = max(0, self.current_cmd_index - 1)
            self.input_widget.setText(self.command_history[self.current_cmd_index])
        return super().eventFilter(source, event)
