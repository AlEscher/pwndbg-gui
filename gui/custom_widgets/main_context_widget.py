import logging
import os
import sys
from typing import TYPE_CHECKING

from PySide6.QtCore import Qt, QThread, Signal, Slot
from PySide6.QtWidgets import QGroupBox, QVBoxLayout, QLineEdit, QHBoxLayout, QPushButton, QLabel

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
    gdb_write = Signal(str, bool)
    gdb_start = Signal(list)
    stop_thread = Signal()
    inferior_write = Signal(bytes)
    inferior_run = Signal()
    update_gui = Signal(str, bytes)

    def __init__(self, parent: 'PwnDbgGui'):
        super().__init__(parent)
        self.update_gui.connect(parent.update_pane)
        self.inferior_thread = QThread()
        self.inferior_handler = InferiorHandler()
        self.buttons_data = {'&r': self.run, '&c': self.continue_execution, '&n': self.next,
                             '&s': self.step, 'ni': self.next_instruction, 'si': self.step_into}
        self.start_update_worker(parent)
        self.output_widget = MainContextOutput(self)
        self.input_widget = QLineEdit(self)
        self.input_widget.returnPressed.connect(self.handle_submit)
        self.buttons = QHBoxLayout()
        self.setup_buttons()
        self.setup_widget_layout()

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
        self.inferior_thread = QThread()
        self.inferior_handler.moveToThread(self.inferior_thread)
        self.inferior_handler.update_gui.connect(parent.update_pane)
        # Allow giving the thread work from outside
        self.gdb_write.connect(parent.gdb_handler.send_command)
        self.inferior_write.connect(self.inferior_handler.inferior_write)
        self.inferior_run.connect(self.inferior_handler.inferior_runs)
        self.inferior_thread.finished.connect(self.inferior_handler.deleteLater)
        # Allow stopping the thread from outside
        self.stop_thread.connect(self.inferior_thread.quit)
        self.inferior_thread.start()

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
        self.gdb_write.emit("r", True)

    @Slot()
    def continue_execution(self):
        logger.debug("Executing c callback")
        self.gdb_write.emit("c", True)

    @Slot()
    def next(self):
        logger.debug("Executing n callback")
        self.gdb_write.emit("n", True)

    @Slot()
    def step(self):
        logger.debug("Executing s callback")
        self.gdb_write.emit("s", True)

    @Slot()
    def next_instruction(self):
        logger.debug("Executing ni callback")
        self.gdb_write.emit("ni", True)

    @Slot()
    def step_into(self):
        logger.debug("Executing si callback")
        self.gdb_write.emit("si", True)

    def submit_cmd(self):
        user_line = self.input_widget.text()
        logger.debug("Sending command '%s' to gdb", user_line)
        self.update_gui.emit("main", f"> {user_line}\n".encode())
        self.gdb_write.emit(user_line, True)
        self.input_widget.clear()

    def submit_input(self):
        user_line = self.input_widget.text()
        self.inferior_write.emit(user_line.encode() + b"\n")
        self.input_widget.clear()

    def cont_handler(self, event):
        # logger.debug("event type: continue (inferior runs)")
        InferiorHandler.INFERIOR_STATE = InferiorState.RUNNING
        self.inferior_run.emit()

    def exit_handler(self, event):
        # logger.debug("event type: exit (inferior exited)")
        InferiorHandler.INFERIOR_STATE = InferiorState.EXITED
        if hasattr(event, 'exit_code'):
            #logger.debug("exit code: %d" % event.exit_code)
            self.update_gui.emit("main", b"Inferior exited with code: " + str(event.exit_code).encode() + b"\n")
        else:
            logger.debug("exit code not available")

    def stop_handler(self, event):
        # logger.debug("event type: stop (inferior stopped)")
        InferiorHandler.INFERIOR_STATE = InferiorState.STOPPED
        if hasattr(event, 'breakpoints'):
            print("Hit breakpoint(s): {} at {}".format(event.breakpoints[0].number, event.breakpoints[0].location))
            print("hit count: {}".format(event.breakpoints[0].hit_count))
        else:
            # logger.debug("no breakpoint was hit")
            pass

    def call_handler(self, event):
        # logger.debug("event type: call (inferior calls function)")
        if hasattr(event, 'address'):
            logger.debug("function to be called at: %s" % hex(event.address))
        else:
            logger.debug("function address not available")
