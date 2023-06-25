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

        # open a tty for interaction with the inferior process (allows for separation of contexts)
        self.master, self.slave = os.openpty()
        # Set the master file descriptor to non-blocking mode
        flags = fcntl.fcntl(self.master, fcntl.F_GETFL)
        fcntl.fcntl(self.master, fcntl.F_SETFL, flags | os.O_NONBLOCK)
        # execute gdb tty command to forward the inferior to this tty
        tty = os.ttyname(self.slave)
        logger.info("Opened tty for inferior interaction: %s", tty)
        gdb.execute('tty ' + tty)

    @Slot()
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

    @Slot()
    def set_target(self, arguments: List[str]):
        """Execute the given command, use for setting the debugging target"""
        logger.info("Setting GDB target to %s", arguments)
        cmd = " ".join(arguments)
        gdb.execute(cmd)

    @Slot()
    def inferior_read(self) -> bytes:
        try:
            inferior_read = os.read(self.master, 4096)
            logger.debug("INFERIOR LOG:")
            logger.debug(inferior_read)
            return inferior_read
        except BlockingIOError:
            # No data available currently
            logger.debug("INFERIOR LOG: EMPTY")
            return b""

    @Slot()
    def inferior_write(self, inferior_input: bytes) -> bytes:
        os.write(self.master, inferior_input)


def cont_handler(event):
    logger.debug("event type: continue (inferior runs)")


def exit_handler(event):
    logger.debug("event type: exit (inferior exited)")
    if hasattr(event, 'exit_code'):
        logger.debug("exit code: %d" % event.exit_code)
    else:
        logger.debug("exit code not available")


def stop_handler(event):
    logger.debug("event type: stop (inferior stopped)")
    if hasattr(event, 'breakpoints'):
        logger.debug("hit breakpoint(s): %d" % event.breakpoints[0].number)
        logger.debug("at %s", event.breakpoints[0].location)
        logger.debug("hit count: %d", event.breakpoints[0].hit_count)
    else:
        logger.debug("no breakpoint was hit")


def call_handler(event):
    logger.debug("event type: call (inferior calls function)")
    if hasattr(event, 'address'):
        logger.debug("function to be called at: %s" % hex(event.address))
    else:
        logger.debug("function address not available")


gdb.events.cont.connect(cont_handler)
gdb.events.exited.connect(exit_handler)
gdb.events.stop.connect(stop_handler)
gdb.events.inferior_call.connect(call_handler)
