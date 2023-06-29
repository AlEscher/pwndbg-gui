import logging
from typing import List

from PySide6.QtCore import QObject, Slot, Signal
from pygdbmi import gdbcontroller
from inferior_state import InferiorState
from inferior_handler import InferiorHandler

from gui import gdb_handler

logger = logging.getLogger(__file__)


# Reader object to continuously check for data from gdb.
class GdbReader(QObject):
    update_gui = Signal(str, bytes)
    inferior_runs = Signal()

    def __init__(self, controller: gdbcontroller.GdbController):
        super().__init__()
        self.controller = controller

    @Slot()
    def read_with_timeout(self):
        while True:
            response = self.controller.get_gdb_response(raise_error_on_timeout=False)
            if response is not None:
                self.parse_response(response)

    def parse_response(self, gdbmi_response: list[dict]):
        result = []
        for response in gdbmi_response:
            if response["type"] == "console" and response["payload"] is not None and response["stream"] == "stdout":
                result.append(response["payload"])
            if response["type"] == "result" and response["message"] == "done":
                if response["token"] is not None:
                    # We found a token -> send it to the corresponding context
                    self.update_gui.emit(token_to_context[response["token"]], "".join(result))
                else:
                    # no token in result -> dropping all previous messages
                    result = []
            if response["type"] == "notify":
                if response["message"] == "running":
                    InferiorHandler.INFERIOR_STATE = InferiorState.RUNNING
                if response["message"] == "stopped":
                    InferiorHandler.INFERIOR_STATE = InferiorState.STOPPED
                if response["message"] == "thread-group-exited":
                    InferiorHandler.INFERIOR_STATE = InferiorState.EXITED
