import logging
from typing import TYPE_CHECKING, List

from PySide6.QtCore import Qt, QThread, Signal

from gui.custom_widgets.context_text_edit import ContextTextEdit
from gui.inferior_handler import InferiorHandler
from gui.gdb_handler import GdbHandler

import gdb

# Prevent circular import error
if TYPE_CHECKING:
    from gui.gui import PwnDbgGui

logger = logging.getLogger(__file__)


class MainTextEdit(ContextTextEdit):
    gdb_write = Signal(str)
    gdb_start = Signal(list)
    stop_thread = Signal()
    inferior_write = Signal(bytes)
    inferior_read = Signal()

    def __init__(self, parent: 'PwnDbgGui', args: List[str]):
        super().__init__(parent)
        self.setReadOnly(False)
        self.update_thread = QThread()
        self.gdb_handler = GdbHandler(active_contexts=parent.seg_to_widget.keys())
        self.inferior_thread = QThread()
        self.inferior_handler = InferiorHandler()
        self.parent = parent
        self.setObjectName("main")
        self.start_update_worker(args)

        gdb.events.cont.connect(self.cont_handler)
        gdb.events.exited.connect(self.exit_handler)
        gdb.events.stop.connect(self.stop_handler)
        gdb.events.inferior_call.connect(self.call_handler)

    def add_content(self, content: str):
        super().add_content(self.toHtml() + content)

    def start_update_worker(self, args: List[str]):
        self.update_thread = QThread()
        self.gdb_handler.moveToThread(self.update_thread)
        self.inferior_thread = QThread()
        self.inferior_handler.moveToThread(self.inferior_thread)
        # Allow the worker to update contexts in the GUI thread
        self.gdb_handler.update_gui.connect(self.parent.update_pane)
        self.inferior_handler.update_gui.connect(self.parent.update_pane)
        # Allow giving the thread work from outside
        self.gdb_write.connect(self.gdb_handler.send_command)
        self.inferior_write.connect(self.inferior_handler.inferior_write)
        self.inferior_read.connect(self.inferior_handler.inferior_read)
        # Thread cleanup
        self.update_thread.finished.connect(self.gdb_handler.deleteLater)
        self.inferior_thread.finished.connect(self.inferior_handler.deleteLater)
        # Allow stopping the thread from outside
        self.stop_thread.connect(self.update_thread.quit)
        self.stop_thread.connect(self.inferior_thread.quit)
        logger.debug("Starting new worker threads in MainTextEdit")
        self.update_thread.start()
        self.inferior_thread.start()
        self.gdb_start.connect(self.gdb_handler.set_target)
        self.gdb_start.emit(args)

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Return or event.key() == Qt.Key_Enter:
            logger.debug("KEYPRESS DETECTED")
            if InferiorHandler.INFERIOR_STATUS == 1:
                # Inferior is running, send to inferior
                self.submit_input()
            else:
                # Enter was pressed, send command to pwndbg
                self.submit_cmd()
        super().keyPressEvent(event)

    def submit_cmd(self):
        lines = self.toPlainText().splitlines(keepends=True)
        if len(lines) > 0:
            cmd = lines[-1]
            cmd = cmd[cmd.find(">") + 1:]
            logger.debug("Sending command '%s' to gdb", cmd)
            self.gdb_write.emit(cmd)
            return
        logger.debug("No lines to send as command!")

    def submit_input(self):
        lines = self.toPlainText().splitlines(keepends=True)
        if len(lines) > 0:
            logger.debug("Sending to Inferior %s", lines[-1])
            self.inferior_write.emit(lines[-1])
            return
        logger.debug("No lines to send to inferior!")

    def cont_handler(self, event):
        # logger.debug("event type: continue (inferior runs)")
        InferiorHandler.INFERIOR_STATUS = 1
        self.inferior_read.emit()
        logger.debug("emitted read")

    def exit_handler(self, event):
        # logger.debug("event type: exit (inferior exited)")
        InferiorHandler.INFERIOR_STATUS = 0
        if hasattr(event, 'exit_code'):
            logger.debug("exit code: %d" % event.exit_code)
        else:
            logger.debug("exit code not available")

    def stop_handler(self, event):
        # logger.debug("event type: stop (inferior stopped)")
        InferiorHandler.INFERIOR_STATUS = 2
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
