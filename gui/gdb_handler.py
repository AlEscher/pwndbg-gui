import logging
from pathlib import Path
from typing import List, Dict, Tuple

from PySide6.QtCore import QObject, Slot, Signal
from pygdbmi import gdbcontroller

from gui.inferior_handler import InferiorHandler
from gui.inferior_state import InferiorState
from tokens import ResponseToken, Context_to_Token
from gui.constants import PwndbgGuiConstants

logger = logging.getLogger(__file__)


class GdbHandler(QObject):
    """A wrapper to interact with GDB/pwndbg via the GDB Machine Interface"""
    update_gui = Signal(str, bytes)

    def __init__(self):
        super().__init__()
        self.past_commands: List[str] = []
        self.contexts = ['regs', 'stack', 'disasm', 'code', 'backtrace']
        self.controller = gdbcontroller.GdbController()
        # active watches in the form of {address: (idx , number of lines)}
        self.watches: Dict[str, List[int]] = {}

    def write_to_controller(self, token: ResponseToken, command: str):
        self.controller.write(str(token) + command, read_response=False)

    def init(self):
        """With GDB MI, the .gdbinit file is ignored so we load it ourselves"""
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
        self.write_to_controller(ResponseToken.GUI_MAIN_CONTEXT, " ".join(["file"] + arguments))
        InferiorHandler.INFERIOR_STATE = InferiorState.QUEUED

    @Slot(list)
    def set_pid_target(self, arguments: List[str]):
        self.write_to_controller(ResponseToken.GUI_MAIN_CONTEXT, " ".join(["attach"] + arguments))
        # Attaching to a running process stops it
        InferiorHandler.INFERIOR_STATE = InferiorState.STOPPED

    @Slot(list)
    def set_source_dir(self, arguments: List[str]):
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
        self.write_to_controller(ResponseToken.GUI_HEAP_HEAP, "heap")

    @Slot()
    def execute_bins_cmd(self):
        self.write_to_controller(ResponseToken.GUI_HEAP_BINS, "bins")

    @Slot(str)
    def execute_try_free(self, param: str):
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
