import logging
import os
import sys
from typing import TYPE_CHECKING, List

from PySide6.QtCore import Qt, QThread, Signal, Slot, QEvent
from PySide6.QtWidgets import QGroupBox, QVBoxLayout, QLineEdit, QHBoxLayout, QPushButton, QLabel, QWidget

sys.path.append(
    os.path.abspath(os.path.join(os.path.dirname(__file__), os.path.pardir)))
from constants import PwndbgGuiConstants
from custom_widgets.main_context_output import MainContextOutput
from inferior_handler import InferiorHandler
from inferior_state import InferiorState

# Prevent circular import error
if TYPE_CHECKING:
    from gui.pwndbg_gui import PwnDbgGui

logger = logging.getLogger(__file__)


class MainContextWidget(QGroupBox):
    gdb_write = Signal(str)
    gdb_start = Signal(list)
    stop_thread = Signal()
    inferior_write = Signal(bytes)
    update_gui = Signal(str, bytes)

    def __init__(self, parent: 'PwnDbgGui'):
        super().__init__(parent)
        self.update_gui.connect(parent.update_pane)
        self.buttons_data = {'&r': self.run, '&c': self.continue_execution, '&n': self.next,
                             '&s': self.step, 'ni': self.next_instruction, 'si': self.step_into}
        self.start_update_worker(parent)
        self.output_widget = MainContextOutput(self)
        self.input_widget = QLineEdit(self)
        self.input_widget.returnPressed.connect(self.handle_submit)
        self.input_widget.installEventFilter(self)
        # The currently selected command in the command history, for when the user presses ↑ and ↓
        self.current_cmd_index = 0
        self.buttons = QHBoxLayout()
        self.setup_buttons()
        self.setup_widget_layout()
        self.command_history: List[str] = [""]

    def setup_widget_layout(self):
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setFlat(True)
        context_layout = QVBoxLayout()
        context_layout.addLayout(self.buttons)
        context_layout.addWidget(self.output_widget)
        input_layout = QHBoxLayout()
        input_layout.addWidget(QLabel(f"<span style=' color:{PwndbgGuiConstants.RED};'>pwndbg></span>"))
        input_layout.addWidget(self.input_widget)
        context_layout.addLayout(input_layout)
        self.setLayout(context_layout)

    def setup_buttons(self):
        self.buttons.setAlignment(Qt.AlignmentFlag.AlignRight)
        for label, callback in self.buttons_data.items():
            button = QPushButton(label)
            button.clicked.connect(callback)
            self.buttons.addWidget(button)

    def start_update_worker(self, parent: 'PwnDbgGui'):
        # Allow giving the thread work from outside
        self.gdb_write.connect(parent.gdb_handler.send_command)
        self.inferior_write.connect(parent.inferior_handler.inferior_write)

    @Slot()
    def handle_submit(self):
        if InferiorHandler.INFERIOR_STATE == InferiorState.RUNNING:
            # Inferior is running, send to inferior
            self.submit_input()
        else:
            # Enter was pressed, send command to pwndbg
            self.submit_cmd()

    @Slot()
    def run(self):
        logger.debug("Executing r callback")
        self.gdb_write.emit("r")

    @Slot()
    def continue_execution(self):
        logger.debug("Executing c callback")
        self.gdb_write.emit("c")

    @Slot()
    def next(self):
        logger.debug("Executing n callback")
        self.gdb_write.emit("n")

    @Slot()
    def step(self):
        logger.debug("Executing s callback")
        self.gdb_write.emit("s")

    @Slot()
    def next_instruction(self):
        logger.debug("Executing ni callback")
        self.gdb_write.emit("ni")

    @Slot()
    def step_into(self):
        logger.debug("Executing si callback")
        self.gdb_write.emit("si")

    def submit_cmd(self):
        user_line = self.input_widget.text()
        if self.command_history[-1] != user_line:
            self.command_history.insert(-1, user_line)
            self.current_cmd_index = len(self.command_history) - 1
        logger.debug("Sending command '%s' to gdb", user_line)
        self.update_gui.emit("main", f"> {user_line}\n".encode())
        self.gdb_write.emit(user_line)
        self.input_widget.clear()

    def submit_input(self):
        user_line = self.input_widget.text()
        self.inferior_write.emit(user_line.encode() + b"\n")
        self.input_widget.clear()

    def eventFilter(self, source: QWidget, event: QEvent):
        # https://stackoverflow.com/a/46506129
        if event.type() != QEvent.Type.KeyPress or source is not self.input_widget:
            return super().eventFilter(source, event)
        if event.key() == Qt.Key.Key_Down:
            self.current_cmd_index = min(len(self.command_history) - 1, self.current_cmd_index + 1)
            if self.current_cmd_index < len(self.command_history):
                self.input_widget.setText(self.command_history[self.current_cmd_index])
        elif event.key() == Qt.Key.Key_Up:
            self.current_cmd_index = max(0, self.current_cmd_index - 1)
            if self.current_cmd_index < len(self.command_history):
                self.input_widget.setText(self.command_history[self.current_cmd_index])
        return super().eventFilter(source, event)
