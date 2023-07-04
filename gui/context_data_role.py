from enum import auto, IntEnum

from PySide6.QtCore import Qt


class ContextDataRole(IntEnum):
    """Custom data role for ContextListWidgets"""
    @staticmethod
    def _generate_next_value_(name, start, count, last_values):
        # Default offset value: https://doc.qt.io/qt-6/qt.html#ItemDataRole-enum
        return Qt.ItemDataRole.UserRole + count

    # Represents an address, e.g. the stack address in a stack context
    ADDRESS = auto()
    # Represents a value, e.g. the value pointed to by a stack address
    VALUE = auto()
