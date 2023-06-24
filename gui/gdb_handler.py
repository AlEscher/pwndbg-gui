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
        self.context_to_func = dict(regs=context_regs, stack=context_stack, disasm=context_disasm, code=context_code,
                                    backtrace=context_backtrace)
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


def cont_handler(event):
    logger.info("event type: continue (inferior runs)")


def exit_handler(event):
    logger.info("event type: exit (inferior exited)")
    if hasattr(event, 'exit_code'):
        logger.info("exit code: %d" % event.exit_code)
    else:
        logger.info("exit code not available")


def stop_handler(event):
    logger.info("event type: stop (inferior stopped)")
    if hasattr(event, 'breakpoints'):
        logger.info("hit breakpoint(s): %d" % event.breakpoints[0].number)
        logger.info("at %s", event.breakpoints[0].location)
        logger.info("hit count: %d", event.breakpoints[0].hit_count)
    else:
        logger.info("no breakpoint was hit")


def call_handler(event):
    logger.info("event type: call (inferior calls function)")
    if hasattr(event, 'address'):
        logger.info("function to be called at: %s" % hex(event.address))
    else:
        logger.info("function address not available")


gdb.events.cont.connect(cont_handler)
gdb.events.exited.connect(exit_handler)
gdb.events.stop.connect(stop_handler)
gdb.events.inferior_call.connect(call_handler)
