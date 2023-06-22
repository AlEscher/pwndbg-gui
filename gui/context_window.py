import logging
import re
from typing import TYPE_CHECKING

from PySide6.QtCore import Qt
from PySide6.QtGui import QFont
from PySide6.QtWidgets import QTextEdit

# Prevent circular import error
if TYPE_CHECKING:
    from gui import PwnDbgGui

logger = logging.getLogger(__file__)


class ContextWindow(QTextEdit):
    def __init__(self, parent: 'PwnDbgGui', ):
        super().__init__(parent)

    def add_gdb_output(self, gdb_output: bytes):
        tokens = gdb_output.split(b"\x1b[")
        self.reset_font()
        for token in tokens:
            self.parse_ascii_control(token)
        self.reset_font()

    def reset_font(self):
        self.setFontWeight(QFont.Weight.Normal)
        self.setTextColor(Qt.GlobalColor.white)

    def parse_ascii_control(self, token: bytes):
        # Remove weird bytes, e.g. in \x01\x1b[31m\x1b[1m\x02pwndbg> \x01\x1b[0m\x1b[31m\x1b[0m\x02
        token = token.replace(b"\x01", b"").replace(b"\x02", b"")
        start = token[:3]
        # https://stackoverflow.com/a/33206814
        # Colors
        if start == b"30m":
            self.setTextColor(Qt.GlobalColor.black)
            self.insertPlainText(token.strip(start).decode())
        elif start == b"31m":
            self.setTextColor(Qt.GlobalColor.darkRed)
            self.insertPlainText(token.strip(start).decode())
        elif start == b"32m":
            self.setTextColor(Qt.GlobalColor.darkGreen)
            self.insertPlainText(token.strip(start).decode())
        elif start == b"33m":
            self.setTextColor(Qt.GlobalColor.darkYellow)
            self.insertPlainText(token.strip(start).decode())
        elif start == b"34m":
            self.setTextColor(Qt.GlobalColor.darkBlue)
            self.insertPlainText(token.strip(start).decode())
        elif start == b"35m":
            self.setTextColor(Qt.GlobalColor.darkMagenta)
            self.insertPlainText(token.strip(start).decode())
        elif start == b"36m":
            self.setTextColor(Qt.GlobalColor.darkCyan)
            self.insertPlainText(token.strip(start).decode())
        elif start == b"37m":
            self.setTextColor(Qt.GlobalColor.white)
            self.insertPlainText(token.strip(start).decode())
        elif start == b"91m":
            # Ignore for now
            pass
        # Font
        elif start.startswith(b"1m"):
            self.setFontWeight(QFont.Weight.Bold)
            self.insertPlainText(token[2:].decode())
        elif start.startswith(b"0m"):
            self.reset_font()
            self.insertPlainText(token[2:].decode())
        else:
            self.insertPlainText(token.decode())
