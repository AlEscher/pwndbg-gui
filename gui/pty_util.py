import os
import pty
import logging
from typing import List, Tuple, Dict

logger = logging.getLogger(__file__)

gdbinit_path = os.path.expanduser("~/.gdbinit")


def create_and_register_context(section: str) -> Tuple[int, int]:
    (master, slave) = pty.openpty()
    logger.info("Opened PTY for %s with master %s and slave %s", section, os.ttyname(master), os.ttyname(slave))
    init_cmd = f"contextoutput(\"{section}\", \"{os.ttyname(slave)}\", True)\n"
    open(gdbinit_path, "a").write(init_cmd)
    return master, slave


def create_pty_devices() -> Dict[str, Tuple[int, int]]:
    """Create one pty for each context, return a list of tuples (master, slave) And register them with pwndbg. See also
    https://github.com/pwndbg/pwndbg/blob/dev/FEATURES.md#splitting--layouting-context"""
    open(gdbinit_path, "a").write("python\nfrom pwndbg.commands.context import contextoutput, output, clear_screen\n")
    pty_devices = dict(map(lambda section: (section, create_and_register_context(section)), ["stack"]))
    open(gdbinit_path, "a").write("end\n")
    return pty_devices


def close_pty_pair(pty_pair: Tuple[int, int]):
    master, slave = pty_pair
    logger.info("Closing %d and %d", os.ttyname(master), os.ttyname(slave))
    os.close(master)
    os.close(slave)
