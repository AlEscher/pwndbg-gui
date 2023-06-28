import logging
from typing import List

# These imports are broken here, but will work via .gdbinit
import gdb
from PySide6.QtCore import QObject, Slot, Signal, QThread
from pwndbg.commands.context import context_stack, context_regs, context_disasm, context_code, context_backtrace

from gui.inferior_handler import InferiorHandler
from gui.inferior_state import InferiorState

from gui.tee import TEE_STDOUT
logger = logging.getLogger(__file__)


def is_target_running():
    # https://sourceware.org/gdb/onlinedocs/gdb/Threads-In-Python.html#Threads-In-Python
    return any([t.is_valid() for t in gdb.selected_inferior().threads()])


def get_fs_base() -> str:
    try:
        logger.debug("Getting fs_base from GDB")
        output: str = gdb.execute("info register fs_base", to_string=True)
        parts = output.split()
        if "fs_base" in output and len(parts) > 1:
            return f"FS  {parts[1]}"
        else:
            return ""
    except gdb.error:
        return ""


class GdbHandler(QObject):
    """A wrapper to interact with GDB/pwndbg via gdb.execute"""
    update_gui = Signal(str, bytes)
    inferior_write = Signal(bytes)
    inferior_run = Signal()

    def __init__(self):
        super().__init__()
        self.past_commands: List[str] = []
        self.context_to_func = dict(regs=context_regs, stack=context_stack, disasm=context_disasm, code=context_code,
                                    backtrace=context_backtrace)
        # setting up inferior thread
        self.inferior_thread = QThread()
        self.inferior_handler = InferiorHandler()
        self.inferior_handler.moveToThread(self.inferior_thread)
        # setting up signals to inferior
        self.inferior_write.connect(self.inferior_handler.inferior_write)
        self.inferior_run.connect(self.inferior_handler.inferior_runs)
        # Allow stopping the thread from outside
        self.inferior_thread.finished.connect(self.inferior_handler.deleteLater)
        #self.stop_thread.connect(self.inferior_thread.quit)


        gdb.events.cont.connect(self.cont_handler)
        gdb.events.exited.connect(self.exit_handler)
        gdb.events.stop.connect(self.stop_handler)
        gdb.events.inferior_call.connect(self.call_handler)

    @Slot(str)
    def send_command(self, cmd: str, capture=True):
        """Execute the given command and then update all context panes"""
        try:
            response = gdb.execute(cmd, from_tty=True, to_string=capture)
        except gdb.error as e:
            logger.warning("Error while executing command '%s': '%s'", cmd, str(e))
            response = str(e) + "\n"
        if capture:
            self.update_gui.emit("main", response.encode())

        catched_tee = TEE_STDOUT.get_output()
        logger.debug("logged from tee: %s", catched_tee)
        #self.update_gui.emit("main", catched_tee.encode())
        if not is_target_running():
            logger.debug("Target not running, skipping context updates")
            return
        # Update contexts
        for context, func in self.context_to_func.items():
            context_data: List[str] = func(with_banner=False)
            self.update_gui.emit(context, "\n".join(context_data).encode())

    @Slot(list)
    def set_target(self, arguments: List[str]):
        """Set the executable target of GDB"""
        """Execute the given command, use for setting the debugging target"""
        logger.info("Setting GDB target to %s", arguments)
        cmd = " ".join(arguments)
        gdb.execute(cmd)

    @Slot(list)
    def change_setting(self, arguments: List[str]):
        """Change a setting. Calls 'set' followed by the provided arguments"""
        logging.debug("Changing gdb setting with parameters: %s", arguments)
        gdb.execute("set " + " ".join(arguments))

    @Slot(int)
    def update_stack_lines(self, new_value: int):
        """Set pwndbg's context-stack-lines to a new value"""
        self.change_setting(["context-stack-lines", str(new_value)])
        context_data: List[str] = context_stack(with_banner=False)
        self.update_gui.emit("stack", "\n".join(context_data).encode())

    @Slot(bytes)
    def submit_to_inferior(self, to_inferior: bytes):
        self.inferior_write.emit(to_inferior)

    # Event handlers for gdb
    def cont_handler(self, event):
        # logger.debug("event type: continue (inferior runs)")
        InferiorHandler.INFERIOR_STATE = InferiorState.RUNNING
        self.inferior_run.emit()

    def exit_handler(self, event):
        # logger.debug("event type: exit (inferior exited)")
        InferiorHandler.INFERIOR_STATE = InferiorState.EXITED
        if hasattr(event, 'exit_code'):
            #logger.debug("exit code: %d" % event.exit_code)
            self.update_gui.emit("main", b"Inferior exited with code: " + str(event.exit_code).encode() + b"\n")
        else:
            logger.debug("exit code not available")

    def stop_handler(self, event):
        # logger.debug("event type: stop (inferior stopped)")
        InferiorHandler.INFERIOR_STATE = InferiorState.STOPPED
        if hasattr(event, 'breakpoints'):
            print("Hit breakpoint(s): {} at {}".format(event.breakpoints[0].number, event.breakpoints[0].location))
            print("hit count: {}".format(event.breakpoints[0].hit_count))
        else:
            # logger.debug("no breakpoint was hit")
            pass

    def call_handler(self, event):
        # logger.debug("event type: call (inferior calls function)")
        if hasattr(event, 'address'):
            logger.debug("function to be called at: %s" % hex(event.address))
        else:
            logger.debug("function address not available")
