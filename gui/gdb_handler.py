import logging
from pathlib import Path
from typing import List

from PySide6.QtCore import QObject, Slot, Signal
from pygdbmi import gdbcontroller

from gui import tokens
from gui.inferior_handler import InferiorHandler
from gui.inferior_state import InferiorState
from tokens import ResponseToken

logger = logging.getLogger(__file__)


def extract_console_payloads(gdbmi_response: list[dict]) -> list[str]:
    result = []
    for response in gdbmi_response:
        if response["type"] == "console" and response["payload"] is not None and response["stream"] == "stdout":
            result.append(response["payload"])
    return result


def find_pwndbg_source_cmd() -> str:
    """Reads the command to load pwndbg from the user's ".gdbinit" file and returns the command"""
    gdbinit = Path(Path.home() / ".gdbinit").resolve()
    if not gdbinit.exists():
        logger.warning("Could not find .gdbinit file at %s", str(gdbinit))
    lines = gdbinit.read_text().splitlines()
    for line in lines:
        if "source" in line and "pwndbg" in line:
            logger.debug("Found pwndbg command: %s", line)
            return line
    logger.warning("Could not find command to load pwndbg in .gdbinit, please check your pwndbg installation")
    return ""


class GdbHandler(QObject):
    """A wrapper to interact with GDB/pwndbg via the GDB Machine Interface"""
    update_gui = Signal(str, bytes)

    def __init__(self):
        super().__init__()
        self.past_commands: List[str] = []
        self.contexts = ['regs', 'stack', 'disasm', 'code', 'backtrace']
        self.controller = gdbcontroller.GdbController()

    def write_to_controller(self, token: ResponseToken, command: str):
        self.controller.write(str(token) + command, read_response=False)

    def init(self):
        """Load pwndbg into gdb. Needs to be called after the GUI has initialized its widgets"""
        self.write_to_controller(ResponseToken.GUI_MAIN_CONTEXT, find_pwndbg_source_cmd())

    @Slot(str)
    def send_command(self, cmd: str):
        """Execute the given command and then update all context panes"""
        try:
            self.write_to_controller(ResponseToken.USER_MAIN, cmd)

            if InferiorHandler.INFERIOR_STATE == InferiorState.RUNNING:
                return
            # Update contexts
            for context in self.contexts:
                self.write_to_controller(tokens.Context_to_Token[context], f"context {context}")
        except Exception as e:
            logger.warning("Error while sending command '%s': '%s'", cmd, str(e))

    @Slot(list)
    def execute_cmd(self, arguments: List[str]):
        """Execute the given command in gdb"""
        self.write_to_controller(ResponseToken.GUI_MAIN_CONTEXT, " ".join(arguments))

    @Slot(list)
    def set_file_target(self, arguments: List[str]):
        self.write_to_controller(ResponseToken.GUI_MAIN_CONTEXT, " ".join(["file"] + arguments))

    @Slot(list)
    def set_pid_target(self, arguments: List[str]):
        self.write_to_controller(ResponseToken.GUI_MAIN_CONTEXT, " ".join(["attach"] + arguments))

    @Slot(list)
    def set_source_dir(self, arguments: List[str]):
        self.write_to_controller(ResponseToken.GUI_MAIN_CONTEXT, " ".join(["attach"] + arguments))

    @Slot(list)
    def change_setting(self, arguments: List[str]):
        """Change a setting. Calls 'set' followed by the provided arguments"""
        logging.debug("Changing gdb setting with parameters: %s", arguments)
        self.write_to_controller(ResponseToken.DELETE, " ".join(["set"] + arguments))

    @Slot(int)
    def update_stack_lines(self, new_value: int):
        """Set pwndbg's context-stack-lines to a new value"""
        self.change_setting(["context-stack-lines", str(new_value)])
        self.write_to_controller(ResponseToken.GUI_STACK_CONTEXT, "context stack")
