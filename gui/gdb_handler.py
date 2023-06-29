import logging
from pathlib import Path
from typing import List

from PySide6.QtCore import QObject, Slot, Signal
from pygdbmi import gdbcontroller

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

    def init(self):
        """Load pwndbg into gdb. Needs to be called after the GUI has initialized its widgets"""
        response = extract_console_payloads(self.controller.write(find_pwndbg_source_cmd()))
        self.update_gui.emit("main", "".join(response).encode())

    @Slot(str)
    def send_command(self, cmd: str, capture=True):
        """Execute the given command and then update all context panes"""
        try:
            responses = self.controller.write(cmd)
            result = extract_console_payloads(responses)
            logger.debug(responses)
        except Exception as e:
            logger.warning("Error while executing command '%s': '%s'", cmd, str(e))
            result = str(e) + "\n"
        if capture:
            self.update_gui.emit("main", "".join(result).encode())

        # Update contexts
        for context in self.contexts:
            responses = self.controller.write(f"context {context}")
            context_data = extract_console_payloads(responses)
            self.update_gui.emit(context, "".join(context_data).encode())

    @Slot(list)
    def execute_cmd(self, arguments: List[str]) -> list[dict]:
        """Execute the given command in gdb"""
        return self.controller.write(" ".join(arguments))

    @Slot(list)
    def set_file_target(self, arguments: List[str]):
        result = extract_console_payloads(self.execute_cmd(["file"] + arguments))
        self.update_gui.emit("main", "".join(result).encode())

    @Slot(list)
    def set_pid_target(self, arguments: List[str]):
        result = extract_console_payloads(self.execute_cmd(["attach"] + arguments))
        self.update_gui.emit("main", "".join(result).encode())

    @Slot(list)
    def set_source_dir(self, arguments: List[str]):
        result = extract_console_payloads(self.execute_cmd(["dir"] + arguments))
        self.update_gui.emit("main", "".join(result).encode())

    @Slot(list)
    def change_setting(self, arguments: List[str]):
        """Change a setting. Calls 'set' followed by the provided arguments"""
        logging.debug("Changing gdb setting with parameters: %s", arguments)
        self.controller.write(" ".join(["set"] + arguments), timeout_sec=0, raise_error_on_timeout=False,
                              read_response=False)

    @Slot(int)
    def update_stack_lines(self, new_value: int):
        """Set pwndbg's context-stack-lines to a new value"""
        self.change_setting(["context-stack-lines", str(new_value)])
        context_data = extract_console_payloads(self.controller.write("context stack"))
        self.update_gui.emit("stack", "".join(context_data).encode())
