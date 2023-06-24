import logging
from typing import List

# These imports are broken here, but will work via .gdbinit
import gdb
from PySide6.QtCore import QObject, Slot, Signal
from pwndbg.commands.context import context_stack, context_regs, context_disasm, context_code, context_backtrace

import PySide6.QtCore
import sys
from io import StringIO

# shit that doesnt work
#qfile = PySide6.QtCore.QFile()
#qfile.open(sys.__stdout__.fileno(), PySide6.QtCore.QFile.OpenMode(0))
#GDB_OUT = PySide6.QtCore.QTextStream(qfile)

# Create a StringIO object to capture the stdout
GDB_OUT = StringIO()
# Redirect sys.stdout to the captured_stdout
#sys.__stdout__ = GDB_OUT
sys.stdout = GDB_OUT


logger = logging.getLogger(__file__)


def is_target_running():
    # https://stackoverflow.com/a/30259980
    return any([t.is_valid() for t in gdb.selected_inferior().threads()])


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
        main_response = GDB_OUT.getvalue()
        logger.info("logged from __stdout__: %s", main_response)
        self.update_gui.emit("main", main_response.encode() + response.encode())

        if not is_target_running():
            return

        # Update contexts
        for context, func in self.context_to_func.items():
            if context in self.active_contexts:
                context_data: List[str] = func()
                self.update_gui.emit(context, "\n".join(context_data).encode())

    @Slot()
    def set_target(self, arguments: List[str]):
        """Execute the given command, use for setting the debugging target"""
        logger.info("Setting GDB target to %s", arguments)
        cmd = " ".join(arguments)
        gdb.execute(cmd)
