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
        for token in tokens:
            self.parse_ascii_control(token)

    def parse_ascii_control(self, token: bytes):
        start = token[:3]
        # Colors
        # https://i.stack.imgur.com/9UVnC.png
        if start == b"30m":
            self.setTextColor(Qt.GlobalColor.black)
            self.insertPlainText(token.strip(start).decode())
        elif start == b"31m":
            self.setTextColor(Qt.GlobalColor.red)
            self.insertPlainText(token.strip(start).decode())
        elif start == b"32m":
            self.setTextColor(Qt.GlobalColor.green)
            self.insertPlainText(token.strip(start).decode())
        elif start == b"33m":
            self.setTextColor(Qt.GlobalColor.yellow)
            self.insertPlainText(token.strip(start).decode())
        elif start == b"34m":
            self.setTextColor(Qt.GlobalColor.blue)
            self.insertPlainText(token.strip(start).decode())
        elif start == b"35m":
            self.setTextColor(Qt.GlobalColor.magenta)
            self.insertPlainText(token.strip(start).decode())
        elif start == b"36m":
            self.setTextColor(Qt.GlobalColor.cyan)
            self.insertPlainText(token.strip(start).decode())
        elif start == b"37m":
            self.setTextColor(Qt.GlobalColor.white)
            self.insertPlainText(token.strip(start).decode())
        # Font
        elif start.startswith(b"1m"):
            self.setFontWeight(QFont.Weight.Bold)
            self.insertPlainText(token[2:].decode())
        elif start.startswith(b"0m"):
            # "Reset"
            self.setFontWeight(QFont.Weight.Normal)
            self.setTextColor(Qt.GlobalColor.white)
            self.insertPlainText(token[2:].decode())
        else:
            self.insertPlainText(token.decode())
