import logging
from typing import List

from PySide6.QtCore import QObject, Slot, Signal, QCoreApplication
from pygdbmi import gdbcontroller
from inferior_state import InferiorState
from inferior_handler import InferiorHandler
import tokens

from gui import gdb_handler

logger = logging.getLogger(__file__)


# Reader object to continuously check for data from gdb.
class GdbReader(QObject):
    update_gui = Signal(str, bytes)
    set_context_stack_lines = Signal(int)
    inferior_runs = Signal()

    def __init__(self, controller: gdbcontroller.GdbController):
        super().__init__()
        self.controller = controller
        self.result = []

    @Slot()
    def read_with_timeout(self):
        while True:
            # first process thread kill events
            QCoreApplication.processEvents()
            response = self.controller.get_gdb_response(raise_error_on_timeout=False)
            if response is not None:
                self.parse_response(response)

    def send_update_gui(self, token: int):
        """Flushes all collected outputs to the destination specified by token"""
        context = tokens.Token_to_Context[token]
        # When the program is not stopped we cannot send commands to gdb, so any context output produced that was not
        # destined to main should not be shown
        if context == tokens.Token_to_Context[tokens.ResponseToken.GUI_MAIN_CONTEXT.value]:
            self.update_gui.emit(context, "".join(self.result).encode())
        elif InferiorHandler.INFERIOR_STATE == InferiorState.STOPPED:
            self.update_gui.emit(context, "".join(self.result).encode())
        self.result = []

    def send_main_update(self):
        """Flushes all collected outputs to the main output window"""
        self.update_gui.emit("main", "".join(self.result).encode())
        self.result = []

    def parse_response(self, gdbmi_response: list[dict]):
        for response in gdbmi_response:
            if response["type"] == "console" and response["payload"] is not None and response["stream"] == "stdout":
                self.result.append(response["payload"])
            if response["type"] == "result" and response["message"] == "done":
                self.handle_result(response)
            if response["type"] == "notify":
                self.handle_notify(response)
            # Ugly way of catching specific log
            if response["type"] == "log" and response["payload"] == "No symbol table is loaded.  Use the \"file\" command.\n":
                self.result.append(response["payload"])


    def handle_result(self, response: dict):
        if response["token"] is not None and response["token"] != 0:
            # We found a token -> send it to the corresponding context
            self.send_update_gui(response["token"])
        else:
            # no token in result -> dropping all previous messages
            self.result = []

    def handle_notify(self, response: dict):
        if response["message"] == "running":
            logger.debug("Setting inferior state to %s", InferiorState.RUNNING.name)
            InferiorHandler.INFERIOR_STATE = InferiorState.RUNNING
            # When we start the inferior we should flush everything we have to main
            self.send_main_update()
        if response["message"] == "stopped":
            # Don't go from EXITED->STOPPED state
            if InferiorHandler.INFERIOR_STATE != InferiorState.EXITED:
                logger.debug("Setting inferior state to %s", InferiorState.STOPPED.name)
                InferiorHandler.INFERIOR_STATE = InferiorState.STOPPED
            '''Stopping due to a breakpoint hit or a step does not give a "result" event, 
            so we have to parse the notify manually and check whether we want to update our current results to the main context widget'''
            if "reason" in response["payload"]:
                if response["payload"]["reason"] == "breakpoint-hit" or response["payload"]["reason"] == "end-stepping-range" or response["payload"]["reason"] == "exited":
                    # This must be treated as a result token, send results to main context output
                    self.send_main_update()
        if response["message"] == "thread-group-exited":
            logger.debug("Setting inferior state to %s", InferiorState.EXITED.name)
            InferiorHandler.INFERIOR_STATE = InferiorState.EXITED
        if response["message"] == "cmd-param-changed" and response["payload"] is not None:
            if response["payload"]["param"] == "context-stack-lines" and InferiorHandler.INFERIOR_STATE == InferiorState.QUEUED:
                self.set_context_stack_lines.emit(int(response["payload"]["value"]))
