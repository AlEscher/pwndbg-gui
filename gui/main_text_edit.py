import logging
from typing import TYPE_CHECKING, List

from PySide6.QtCore import Qt, QThread, Signal

from gui.custom_widgets.context_text_edit import ContextTextEdit
from gui.inferior_handler import InferiorHandler
from gui.gdb_handler import GdbHandler

import gdb

from gui.inferior_state import InferiorState

# Prevent circular import error
if TYPE_CHECKING:
    from gui.gui import PwnDbgGui

logger = logging.getLogger(__file__)


class MainTextEdit(ContextTextEdit):
    gdb_write = Signal(str, bool)
    gdb_start = Signal(list)
    stop_thread = Signal()
    inferior_write = Signal(bytes)
    inferior_read = Signal()

    def __init__(self, parent: 'PwnDbgGui'):
        super().__init__(parent)
        self.setReadOnly(False)
        self.inferior_thread = QThread()
        self.inferior_handler = InferiorHandler()
        self.parent = parent
        self.setObjectName("main")
        self.start_update_worker()

        gdb.events.cont.connect(self.cont_handler)
        gdb.events.exited.connect(self.exit_handler)
        gdb.events.stop.connect(self.stop_handler)
        gdb.events.inferior_call.connect(self.call_handler)

    def add_content(self, content: str):
        super().add_content(self.toHtml() + content)

    def start_update_worker(self):
        self.inferior_thread = QThread()
        self.inferior_handler.moveToThread(self.inferior_thread)
        self.inferior_handler.update_gui.connect(self.parent.update_pane)
        # Allow giving the thread work from outside
        self.gdb_write.connect(self.parent.gdb_handler.send_command)
        self.inferior_write.connect(self.inferior_handler.inferior_write)
        self.inferior_read.connect(self.inferior_handler.inferior_read)
        self.inferior_thread.finished.connect(self.inferior_handler.deleteLater)
        # Allow stopping the thread from outside
        self.stop_thread.connect(self.inferior_thread.quit)
        self.inferior_thread.start()

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Return or event.key() == Qt.Key_Enter:
            if InferiorHandler.INFERIOR_STATE == 1:
                # Inferior is running, send to inferior
                self.submit_input()
            else:
                # Enter was pressed, send command to pwndbg
                self.submit_cmd()
        super().keyPressEvent(event)

    def submit_cmd(self):
        lines = self.toPlainText().splitlines(keepends=True)
        if len(lines) > 0:
            cmd = lines[-1].replace("\n", "")
            logger.debug("Sending command '%s' to gdb", cmd)
            # Do not capture gdb output to a string variable for commands that can change the inferior state
            capture: bool = cmd not in ["c", "r", "n", "ni", "si", "s"]
            self.gdb_write.emit(cmd, capture)
            return
        logger.debug("No lines to send as command!")

    def submit_input(self):
        lines = self.toPlainText().splitlines(keepends=True)
        if len(lines) > 0:
            user_input = lines[-1]
            logger.debug("Sending input '%s' to inferior", user_input)
            self.inferior_write.emit(user_input)
            return
        logger.debug("No lines to send to inferior!")

    def cont_handler(self, event):
        # logger.debug("event type: continue (inferior runs)")
        InferiorHandler.INFERIOR_STATE = InferiorState.RUNNING
        self.inferior_read.emit()
        logger.debug("emitted read")

    def exit_handler(self, event):
        # logger.debug("event type: exit (inferior exited)")
        InferiorHandler.INFERIOR_STATE = InferiorState.EXITED
        if hasattr(event, 'exit_code'):
            logger.debug("exit code: %d" % event.exit_code)
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
