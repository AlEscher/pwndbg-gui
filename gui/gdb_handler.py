import logging
from typing import List

# These imports are broken here, but will work via .gdbinit
import gdb
from PySide6.QtCore import QObject, Slot, Signal
from pwndbg.commands.context import context_stack, context_regs, context_disasm, context_code, context_backtrace

import os
import fcntl

logger = logging.getLogger(__file__)


def is_target_running():
    # https://sourceware.org/gdb/onlinedocs/gdb/Threads-In-Python.html#Threads-In-Python
    return any([t.is_valid() for t in gdb.selected_inferior().threads()])


class GdbHandler(QObject):
    update_gui = Signal(str, bytes)

    def __init__(self, active_contexts: List[str]):
        super().__init__()
        self.past_commands: List[str] = []
        self.context_to_func = dict(regs=context_regs, stack=context_stack, disasm=context_disasm, code=context_code,
                                    backtrace=context_backtrace)
        self.active_contexts = active_contexts

    @Slot(str)
    def send_command(self, cmd: str):
        response = gdb.execute(cmd, from_tty=True, to_string=True)
        self.update_gui.emit("main", response.encode())

        if not is_target_running():
            return
        # Update contexts
        self.inferior_read()
        for context, func in self.context_to_func.items():
            if context in self.active_contexts:
                context_data: List[str] = func(with_banner=False)
                self.update_gui.emit(context, "\n".join(context_data).encode())

    @Slot(list)
    def set_target(self, arguments: List[str]):
        """Execute the given command, use for setting the debugging target"""
        logger.info("Setting GDB target to %s", arguments)
        cmd = " ".join(arguments)
        gdb.execute(cmd)
