import logging
from typing import List

# These imports are broken here, but will work via .gdbinit
from PySide6.QtCore import QObject, Slot, Signal
from pygdbmi import gdbcontroller

logger = logging.getLogger(__file__)


class GdbHandler(QObject):
    """A wrapper to interact with GDB/pwndbg via gdb.execute"""
    update_gui = Signal(str, bytes)

    def __init__(self):
        super().__init__()
        self.past_commands: List[str] = []
        self.contexts = ['regs', 'stack', 'disasm', 'code', 'backtrace']
        self.controller = gdbcontroller.GdbController()

    @Slot(str)
    def send_command(self, cmd: str, capture=True):
        """Execute the given command and then update all context panes"""
        try:
            response = self.controller.write(cmd)
        except Exception as e:
            logger.warning("Error while executing command '%s': '%s'", cmd, str(e))
            response = str(e) + "\n"
        if capture:
            self.update_gui.emit("main", response.encode())

        # Update contexts
        for context in self.contexts:
            context_data: List[str] = self.controller.write(f"context {context}")
            self.update_gui.emit(context, "\n".join(context_data).encode())

    @Slot(list)
    def execute_cmd(self, arguments: List[str]):
        """Execute the given command in gdb"""
        self.controller.write(" ".join(arguments), read_response=True)

    @Slot(list)
    def set_file_target(self, arguments: List[str]):
        self.execute_cmd(["file"] + arguments)

    @Slot(list)
    def set_pid_target(self, arguments: List[str]):
        self.execute_cmd(["attach"] + arguments)

    @Slot(list)
    def set_source_dir(self, arguments: List[str]):
        self.execute_cmd(["dir"] + arguments)

    @Slot(list)
    def change_setting(self, arguments: List[str]):
        """Change a setting. Calls 'set' followed by the provided arguments"""
        logging.debug("Changing gdb setting with parameters: %s", arguments)
        self.controller.write(" ".join(["set"] + arguments), timeout_sec=0, raise_error_on_timeout=False, read_response=False)

    @Slot(int)
    def update_stack_lines(self, new_value: int):
        """Set pwndbg's context-stack-lines to a new value"""
        self.change_setting(["context-stack-lines", str(new_value)])
        context_data: List[str] = self.controller.write("context stack")
        self.update_gui.emit("stack", "\n".join(context_data).encode())
