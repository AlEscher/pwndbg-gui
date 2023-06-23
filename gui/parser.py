from typing import List

from PySide6.QtCore import Qt
from PySide6.QtGui import QFont
from PySide6.QtWidgets import QTextEdit


class ContextParser:
    def __init__(self):
        # Misuse QTextEdit as a HTML parser
        self.parser = QTextEdit()

    def parse(self, raw_output: bytes):
        self.parser.clear()
        tokens = raw_output.split(b"\x1b[")
        self.reset_font()
        for token in tokens:
            self.parse_ascii_control(token)
        self.reset_font()

    def to_html(self, raw_output: bytes) -> str:
        self.parse(raw_output)
        return self.parser.toHtml()

    def reset_font(self):
        self.parser.setFontWeight(QFont.Weight.Normal)
        self.parser.setTextColor(Qt.GlobalColor.white)

    def parse_ascii_control(self, token: bytes):
        # Remove weird bytes, e.g. in \x01\x1b[31m\x1b[1m\x02pwndbg> \x01\x1b[0m\x1b[31m\x1b[0m\x02
        token = token.replace(b"\x01", b"").replace(b"\x02", b"")
        start = token[:3]
        # https://stackoverflow.com/a/33206814
        # Colors
        if start == b"30m":
            self.parser.setTextColor(Qt.GlobalColor.black)
            self.parser.insertPlainText(token.strip(start).decode())
        elif start == b"31m":
            self.parser.setTextColor(Qt.GlobalColor.darkRed)
            self.parser.insertPlainText(token.strip(start).decode())
        elif start == b"32m":
            self.parser.setTextColor(Qt.GlobalColor.darkGreen)
            self.parser.insertPlainText(token.strip(start).decode())
        elif start == b"33m":
            self.parser.setTextColor(Qt.GlobalColor.darkYellow)
            self.parser.insertPlainText(token.strip(start).decode())
        elif start == b"34m":
            self.parser.setTextColor(Qt.GlobalColor.darkBlue)
            self.parser.insertPlainText(token.strip(start).decode())
        elif start == b"35m":
            self.parser.setTextColor(Qt.GlobalColor.darkMagenta)
            self.parser.insertPlainText(token.strip(start).decode())
        elif start == b"36m":
            self.parser.setTextColor(Qt.GlobalColor.darkCyan)
            self.parser.insertPlainText(token.strip(start).decode())
        elif start == b"37m":
            self.parser.setTextColor(Qt.GlobalColor.white)
            self.parser.insertPlainText(token.strip(start).decode())
        elif start == b"91m":
            # Ignore for now
            pass
        # Font
        elif start.startswith(b"1m"):
            self.parser.setFontWeight(QFont.Weight.Bold)
            self.parser.insertPlainText(token[2:].decode())
        elif start.startswith(b"0m"):
            self.reset_font()
            self.parser.insertPlainText(token[2:].decode())
        else:
            self.parser.insertPlainText(token.decode())
