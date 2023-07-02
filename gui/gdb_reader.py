import logging

from PySide6.QtCore import QObject, Slot, Signal, QCoreApplication
from pygdbmi import gdbcontroller

import tokens
from inferior_handler import InferiorHandler
from inferior_state import InferiorState

logger = logging.getLogger(__file__)


# Reader object to continuously check for data from gdb.
class GdbReader(QObject):
    update_gui = Signal(str, bytes)
    send_heap_try_free_response = Signal(bytes)
    send_heap_heap_response = Signal(bytes)
    send_heap_bins_response = Signal(bytes)
    send_watches_hexdump_response = Signal(int, bytes)
    # Send the fs base to the "regs" context
    send_fs_base_response = Signal(bytes)
    send_pwndbg_about = Signal(bytes)
    send_xinfo = Signal(bytes)
    # Emitted when the inferior state changes. True for Stopped and False for Running
    inferior_state_changed = Signal(bool)

    def __init__(self, controller: gdbcontroller.GdbController):
        super().__init__()
        self.controller = controller
        self.result = []
        self.run = True

    @Slot()
    def read_with_timeout(self):
        while self.run:
            # first process thread kill events
            QCoreApplication.processEvents()
            response = self.controller.get_gdb_response(raise_error_on_timeout=False)
            if response is not None:
                self.parse_response(response)

    @Slot()
    def set_run(self, state: bool):
        self.run = state

    def send_update_gui(self, token: int):
        """Flushes all collected outputs to the destination specified by token"""
        if len(self.result) == 0:
            return
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

    def send_context_update(self, signal: Signal, send_on_stop=True):
        """Emit a supplied signal with the collected output"""
        if not send_on_stop:
            # Send this signal even if the inferior is not started yet or running
            signal.emit("".join(self.result).encode())
        elif InferiorHandler.INFERIOR_STATE == InferiorState.STOPPED:
            signal.emit("".join(self.result).encode())
        self.result = []

    def parse_response(self, gdbmi_response: list[dict]):
        for response in gdbmi_response:
            if response["type"] == "console" and response["payload"] is not None and response["stream"] == "stdout":
                self.result.append(response["payload"])
            elif response["type"] == "result":
                self.handle_result(response)
            elif response["type"] == "notify":
                self.handle_notify(response)
            # Ugly way of catching specific log
            elif response["type"] == "log" and response[
                "payload"] == "No symbol table is loaded.  Use the \"file\" command.\n":
                self.result.append(response["payload"])

    def handle_result(self, response: dict):
        if response["token"] is None:
            self.result = []
            return
        if response["message"] == "error" and response["payload"] is not None:
            self.result.append(response["payload"]["msg"])
        token = response["token"]
        if token == tokens.ResponseToken.GUI_HEAP_TRY_FREE:
            self.send_context_update(self.send_heap_try_free_response)
        elif token == tokens.ResponseToken.GUI_HEAP_HEAP:
            self.send_context_update(self.send_heap_heap_response)
        elif token == tokens.ResponseToken.GUI_HEAP_BINS:
            self.send_context_update(self.send_heap_bins_response)
        elif token == tokens.ResponseToken.GUI_REGS_FS_BASE:
            self.send_context_update(self.send_fs_base_response)
        elif token == tokens.ResponseToken.GUI_PWNDBG_ABOUT:
            self.send_context_update(self.send_pwndbg_about, send_on_stop=False)
        elif token == tokens.ResponseToken.GUI_XINFO:
            self.send_context_update(self.send_xinfo)
        elif token >= tokens.ResponseToken.GUI_WATCHES_HEXDUMP:
            if InferiorHandler.INFERIOR_STATE == InferiorState.STOPPED:
                self.send_watches_hexdump_response.emit(token, "".join(self.result).encode())
            self.result = []
        elif token != tokens.ResponseToken.DELETE:
            # We found a context token -> send it to the corresponding context
            self.send_update_gui(token)
        else:
            # no token in result -> dropping all previous messages
            self.result = []

    def handle_notify(self, response: dict):
        if response["message"] == "running":
            logger.debug("Setting inferior state to %s", InferiorState.RUNNING.name)
            InferiorHandler.INFERIOR_STATE = InferiorState.RUNNING
            # When we start the inferior we should flush everything we have to main
            self.send_main_update()
            self.inferior_state_changed.emit(False)
        elif response["message"] == "stopped":
            # Don't go from EXITED->STOPPED state
            self.inferior_state_changed.emit(True)
            if InferiorHandler.INFERIOR_STATE != InferiorState.EXITED:
                logger.debug("Setting inferior state to %s", InferiorState.STOPPED.name)
                InferiorHandler.INFERIOR_STATE = InferiorState.STOPPED
            '''Stopping due to a breakpoint hit or a step does not give a "result" event, 
            so we have to parse the notify manually and check whether we want to update our current results to the main context widget'''
            if "reason" in response["payload"]:
                if response["payload"]["reason"] == "breakpoint-hit" or response["payload"][
                    "reason"] == "end-stepping-range" or response["payload"]["reason"] == "exited":
                    # This must be treated as a result token, send results to main context output
                    self.send_main_update()
        elif response["message"] == "thread-group-exited":
            logger.debug("Setting inferior state to %s", InferiorState.EXITED.name)
            InferiorHandler.INFERIOR_STATE = InferiorState.EXITED
