import logging
from typing import List

from PySide6.QtCore import QObject, Slot, Signal, QCoreApplication
from pygdbmi import gdbcontroller

import gui.tokens as tokens
from gui.inferior_handler import InferiorHandler
from gui.inferior_state import InferiorState

logger = logging.getLogger(__file__)


class GdbReader(QObject):
    """Reader object to continuously check for data from gdb and handle the parsed responses"""
    # Update a context pane in the GUI with data
    update_gui = Signal(str, bytes)
    # Send the result of a try_free command to the Heap widget
    send_heap_try_free_response = Signal(bytes)
    # Send the result of a heap command to the Heap widget
    send_heap_heap_response = Signal(bytes)
    # Send the result of a bins command to the Heap widget
    send_heap_bins_response = Signal(bytes)
    # Send the result of the hexdump output of a watch to the Watches widget
    send_watches_hexdump_response = Signal(int, bytes)
    # Send the fs base to the "regs" context
    send_fs_base_response = Signal(bytes)
    # Send the overview of all pwndbg commands to the GUI
    send_pwndbg_about = Signal(bytes)
    # Send the result of an xinfo command to a list widget
    send_xinfo = Signal(bytes)
    # Emitted when the inferior state changes. True for Stopped and False for Running
    inferior_state_changed = Signal(bool)

    def __init__(self, controller: gdbcontroller.GdbController):
        super().__init__()
        self.controller = controller
        self.result = []
        # Whether the thread should keep working
        self.run = True
        # Some import information like error output of pwndbg commands or even GDB's own commands is only outputted
        # as "log" elements. However, since also all inputted commands are echoed back as logs, we capture logs
        # separately and decide on a "result" element whether we want to forward the logs or not
        self.logs: List[str] = []

    @Slot()
    def read_with_timeout(self):
        """Start continuously reading output from GDB MI"""
        while self.run:
            QCoreApplication.processEvents()
            response = self.controller.get_gdb_response(raise_error_on_timeout=False)
            if response is not None:
                self.parse_response(response)

    @Slot()
    def set_run(self, state: bool):
        """
        Sets whether the thread should keep working
        :param state: True if the thread should keep working
        """
        self.run = state

    def send_update_gui(self, token: int):
        """
        Flushes all collected outputs to the destination specified by token
        :param token: Token of the context pane
        """
        if len(self.result) and len(self.logs) == 0:
            return
        context = tokens.Token_to_Context[token]
        # If we want to send an update but have no results and only logs, it means something went wrong,
        # and we want to forward the output to the user. If we do have results, prioritize them over the logs
        if len(self.result) > 0:
            content = "".join(self.result).encode()
        else:
            # We skip the first log as it is (always?) just the inputted command echoed back
            content = "".join(self.logs[1:]).encode()
        # When the program is not stopped we cannot send commands to gdb, so any context output produced that was not
        # destined to main should not be shown
        if context == tokens.Token_to_Context[tokens.ResponseToken.GUI_MAIN_CONTEXT.value]:
            self.update_gui.emit(context, content)
        elif InferiorHandler.INFERIOR_STATE == InferiorState.STOPPED:
            self.update_gui.emit(context, content)
        self.result = []

    def send_main_update(self):
        """Flushes all collected outputs to the main output window"""
        self.update_gui.emit("main", "".join(self.result).encode())
        self.result = []

    def send_context_update(self, signal: Signal, send_on_stop=True):
        """
        Emit a supplied signal with the collected output
        :param signal: The signal that will handle the data
        :param send_on_stop: Whether to send data only when the inferior is stopped
        """
        if not send_on_stop:
            # Send this signal even if the inferior is not started yet or running
            signal.emit("".join(self.result).encode())
        elif InferiorHandler.INFERIOR_STATE == InferiorState.STOPPED:
            signal.emit("".join(self.result).encode())
        self.result = []

    def parse_response(self, gdbmi_response: list[dict]):
        """
        Parse a response received from GDB MI and decide how to handle it
        :param gdbmi_response: The parsed response from pygdbmi
        """
        for response in gdbmi_response:
            if response["type"] == "console" and response["payload"] is not None and response["stream"] == "stdout":
                self.result.append(response["payload"])
                # When a subprocess is spawned, we get no proper notify/result event from GDB, so we check manually
                if response["payload"].startswith("Detaching"):
                    self.send_main_update()
            elif response["type"] == "output":
                # We always append "output": If the process is started by GDB, our inferior handler will capture all
                # inferior output in his tty, so this code will never be triggered. If the user attaches to a
                # process, the TTY approach does not work, so we will collect the output here instead. The output is
                # sometimes broken, i.e. it contains data that was printed by pwndbg/gdb, however this is a
                # limitation with GDB/Pygdbmi which we cannot fix
                self.result.append(response["payload"])
            elif response["type"] == "result":
                self.handle_result(response)
            elif response["type"] == "notify":
                self.handle_notify(response)
            elif response["type"] == "log":
                self.logs.append(response["payload"])

    def handle_result(self, response: dict):
        """
        Handle messages of the result type, which are emitted after a command/action has finished producing output
        :param response: GDB-MI response with ["type"] == result
        """
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
                ''' Here we send the result of the hexdump, the signal differs from the rest here since we need to send 
                the token as well so that the watch-widget knows to which watch the result belongs. If we have logs then 
                something was wrong with the hexdump command. In this case the logs that describe the error will always 
                be from the third log line onwards.'''
                self.send_watches_hexdump_response.emit(token, "".join(self.result + self.logs[2:]).encode())
            self.result = []
        elif token != tokens.ResponseToken.DELETE:
            # We found a context token -> send it to the corresponding context
            self.send_update_gui(token)
        else:
            # no token in result -> dropping all previous messages
            self.result = []
        self.logs = []

    def handle_notify(self, response: dict):
        """
        Handle the notify events, which are emitted for different occasions
        :param response: GDB-MI response with ["type"] == notify
         """
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
            # If we get a stop we don't get a result type done, which is why we trigger a main context update manually
            self.send_main_update()
        elif response["message"] == "thread-group-exited":
            logger.debug("Setting inferior state to %s", InferiorState.EXITED.name)
            InferiorHandler.INFERIOR_STATE = InferiorState.EXITED
        # If we attach while having a process open we will get a thread-group-exited to indicate the exit of the current
        # process. However, we don't get a running message when attaching for the second time, but only a stopped
        # message. Since we don't switch from exited -> stopped our contexts will not update although they got new
        # information. Solution: interpret thread-group-started notify as running state change.
        elif response["message"] == "thread-group-started":
            logger.debug("Setting inferior state to %s", InferiorState.RUNNING.name)
            InferiorHandler.INFERIOR_STATE = InferiorState.RUNNING
