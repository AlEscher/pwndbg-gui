import logging
import os
import tempfile
from typing import List, Dict

logger = logging.getLogger(__file__)

gdbinit_path = os.path.expanduser("~/.gdbinit")


def create_and_register_context(section: str) -> str:
    pipe = tempfile.mktemp(prefix=f"pwndbgGUI-{section}-", suffix=".tmp")
    os.mkfifo(path=pipe)
    logger.info("Created pipe for %s as %s", section, pipe)
    init_cmd = f"contextoutput(\"{section}\", \"{pipe}\", False)\n"
    open(gdbinit_path, "a").write(init_cmd)
    return pipe


def create_pipes(contexts: List[str]) -> Dict[str, str]:
    """Create one pty for each context, return a list of tuples (master, slave) And register them with pwndbg. See also
    https://github.com/pwndbg/pwndbg/blob/dev/FEATURES.md#splitting--layouting-context"""
    open(gdbinit_path, "a").write("python\nfrom pwndbg.commands.context import contextoutput, output, clear_screen\n")
    pipes = dict(map(lambda section: (section, create_and_register_context(section)), contexts))
    open(gdbinit_path, "a").write("end\n")
    return pipes


def delete_pipe(pipe: str):
    logger.debug("Deleting %s", pipe)
    os.remove(pipe)
