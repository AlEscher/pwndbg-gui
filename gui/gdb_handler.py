import logging
from pathlib import Path
from typing import List, Dict

from PySide6.QtCore import QObject, Slot, Signal
from pygdbmi import gdbcontroller

from gui.constants import PwndbgGuiConstants
from gui.inferior_handler import InferiorHandler
from gui.inferior_state import InferiorState
from gui.tokens import ResponseToken, Context_to_Token

logger = logging.getLogger(__file__)


class GdbHandler(QObject):
    """A wrapper to interact with GDB/pwndbg via the GDB Machine Interface"""
    update_gui = Signal(str, bytes)

    def __init__(self):
        super().__init__()
        self.past_commands: List[str] = []
        self.contexts = ['regs', 'stack', 'disasm', 'code', 'backtrace']
        self.controller = gdbcontroller.GdbController()
        # active watches in the form of {address: [idx , number of lines]}
        self.watches: Dict[str, List[int]] = {}

    def write_to_controller(self, token: ResponseToken, command: str):
        """Wrapper for writing a command to GDB MI with the specified token"""
        self.controller.write(str(token) + command, read_response=False)

    def init(self):
        """Load the user's .gdbinit, check that pwndbg is loaded"""
        # With GDB MI, the .gdbinit file is ignored so we load it ourselves
        gdbinit = Path(Path.home() / ".gdbinit").resolve()
        if not gdbinit.exists():
            logger.warning("Could not find .gdbinit file at %s", str(gdbinit))
            return
        lines = gdbinit.read_text().splitlines()
        pwndbg_loaded = False
        for line in lines:
            if not line.strip():
                continue
            logger.debug("Executing .gdbinit command %s", line)
            self.write_to_controller(ResponseToken.GUI_MAIN_CONTEXT, line)
            if "source" in line and "pwndbg" in line:
                logger.debug("Found pwndbg command: %s", line)
                pwndbg_loaded = True

        if not pwndbg_loaded:
            logger.error("Could not find command to load pwndbg in .gdbinit, please check your pwndbg installation")
        else:
            # Get an overview of all available commands
            self.write_to_controller(ResponseToken.GUI_PWNDBG_ABOUT, "pwndbg --all")

    @Slot(str)
    def send_command(self, cmd: str):
        """Execute the given command and then update all context panes"""
        try:
            self.write_to_controller(ResponseToken.USER_MAIN, cmd)
            # Update contexts
            for context in self.contexts:
                self.write_to_controller(Context_to_Token[context], f"context {context}")
            # Update heap
            self.write_to_controller(ResponseToken.GUI_HEAP_HEAP, "heap")
            self.write_to_controller(ResponseToken.GUI_HEAP_BINS, "bins")
            self.write_to_controller(ResponseToken.GUI_REGS_FS_BASE, "fsbase")
            # Update watches
            logger.debug("updating watches: ")
            for watch, params in self.watches.items():
                logger.debug("updating watch: %s", watch)
                self.write_to_controller(ResponseToken.GUI_WATCHES_HEXDUMP + params[0], " ".join(["hexdump", watch, str(params[1])]))
        except Exception as e:
            logger.warning("Error while sending command '%s': '%s'", cmd, str(e))

    @Slot(list)
    def execute_cmd(self, arguments: List[str]):
        """Execute the given command in gdb"""
        self.write_to_controller(ResponseToken.GUI_MAIN_CONTEXT, " ".join(arguments))

    @Slot(list)
    def set_file_target(self, arguments: List[str]):
        """Load the executable specified by a file path"""
        self.write_to_controller(ResponseToken.GUI_MAIN_CONTEXT, " ".join(["file"] + arguments))
        InferiorHandler.INFERIOR_STATE = InferiorState.QUEUED

    @Slot(list)
    def set_pid_target(self, arguments: List[str]):
        """Attach to the given PID argument"""
        self.write_to_controller(ResponseToken.GUI_MAIN_CONTEXT, " ".join(["attach"] + arguments))
        # Attaching to a running process stops it
        InferiorHandler.INFERIOR_STATE = InferiorState.STOPPED

    @Slot(list)
    def set_source_dir(self, arguments: List[str]):
        """Add a directory where GDB should look for source files"""
        self.write_to_controller(ResponseToken.GUI_MAIN_CONTEXT, " ".join(["dir"] + arguments))

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

    @Slot()
    def execute_heap_cmd(self):
        """Execute the "heap" command"""
        self.write_to_controller(ResponseToken.GUI_HEAP_HEAP, "heap")

    @Slot()
    def execute_bins_cmd(self):
        """Execute the "bins" command"""
        self.write_to_controller(ResponseToken.GUI_HEAP_BINS, "bins")

    @Slot(str)
    def execute_try_free(self, param: str):
        """Execute the "try_free" command with the given address"""
        self.write_to_controller(ResponseToken.GUI_HEAP_TRY_FREE, " ".join(["try_free", param]))

    @Slot(str, int)
    def add_watch(self, param: str, idx: int):
        self.watches[param] = [idx, PwndbgGuiConstants.DEFAULT_WATCH_BYTES]
        logger.debug("Added to watchlist: %s with index %d", param, idx)
        self.write_to_controller(ResponseToken.GUI_WATCHES_HEXDUMP + idx,
                                 " ".join(["hexdump", param, str(PwndbgGuiConstants.DEFAULT_WATCH_BYTES)]))

    @Slot(str)
    def del_watch(self, param: str):
        logger.debug("Deleted watch %s with index %d", param, self.watches[param][0])
        del self.watches[param]

    @Slot(str, int)
    def change_watch_lines (self, param: str, lines: int):
        self.watches[param][1] = lines
        logger.debug("Adapted line count for watch %s to %d", param, lines)
        self.write_to_controller(ResponseToken.GUI_WATCHES_HEXDUMP + self.watches[param][0],
                                 " ".join(["hexdump", param, str(lines)]))

    @Slot(bytes)
    def execute_xinfo(self, address: str):
        """Execute the "xinfo" command with the given address"""
        self.write_to_controller(ResponseToken.GUI_XINFO, " ".join(["xinfo", address]))

    @Slot(str)
    def set_tty(self, tty: str):
        """Execute the "tty" command with the given tty path. GDB will route future inferiors' I/O via this tty"""
        self.write_to_controller(ResponseToken.DELETE, " ".join(["tty", tty]))
