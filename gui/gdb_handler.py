import logging
from typing import List

# These imports are broken here, but will work via .gdbinit
import gdb
from PySide6.QtCore import QObject, Slot, Signal
from pwndbg.commands.context import context_stack, context_regs, context_disasm, context_code, context_backtrace

logger = logging.getLogger(__file__)


class GdbHandler(QObject):
    update_gui = Signal(str, bytes)

    def __init__(self, active_contexts: List[str]):
        super().__init__()
        self.past_commands: List[str] = []
        self.context_to_func = dict(regs=context_regs, stack=context_stack, disasm=context_disasm, code=context_code, backtrace=context_backtrace)
        self.active_contexts = active_contexts

    @Slot()
    def send_command(self, cmd: str):
        response = gdb.execute(cmd, from_tty=True, to_string=True)
        self.update_gui.emit("main", response.encode())
        # Update contexts
        for context, func in self.context_to_func.items():
            if context in self.active_contexts:
                context_data: List[str] = func()
                self.update_gui.emit(context, "\n".join(context_data).encode())

    @Slot()
    def start_gdb(self, arguments: List[str]):
        """Runs gdb with the given program and waits for gdb to have started"""
        logger.info("Setting GDB target to %s", arguments)
        cmd = " ".join(arguments)
        gdb.execute(cmd)
