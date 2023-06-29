from enum import Enum


class InferiorState(Enum):
    # Inferior exited
    EXITED = 0
    # Inferior is running, GDB input is blocked during this time
    RUNNING = 1
    # Inferior is stopped, e.g. by a breakpoint
    STOPPED = 2
    # Inferior is loaded, but not started
    QUEUED = 3
