from PySide6.QtCore import Qt
from PySide6.QtGui import QFont, QColor
from PySide6.QtWidgets import QTextEdit

from constants import PwndbgGuiConstants

import logging
logger = logging.getLogger(__file__)

class ContextParser:
    """Parses raw output from gdb/pwndbg containing ASCII control characters into equivalent HTML code"""
    def __init__(self):
        # Misuse QTextEdit as a HTML parser
        self.parser = QTextEdit()

    def reset(self):
        self.parser.clear()
        self.reset_font()

    def parse(self, raw_output: bytes, remove_headers=False):
        self.reset()
        if remove_headers:
            lines = raw_output.split(b"\n")
            updated_lines = lines[2:][:-2]
            raw_output = b"\n".join(updated_lines)


        tokens = raw_output.split(b"\x1b[")
        for token in tokens:
            self.parse_ascii_control(token)
        self.reset_font()

    def to_html(self, raw_output: bytes, remove_headers=False) -> str:
        self.parse(raw_output, remove_headers)
        return self.parser.toHtml()

    def reset_font(self):
        self.parser.setFontWeight(QFont.Weight.Normal)
        self.parser.setTextColor(Qt.GlobalColor.white)
        self.parser.setFontUnderline(False)
        self.parser.setFontItalic(False)

    def parse_ascii_control(self, token: bytes):
        # Remove weird bytes, e.g. in \x01\x1b[31m\x1b[1m\x02pwndbg> \x01\x1b[0m\x1b[31m\x1b[0m\x02
        token = token.replace(b"\x01", b"").replace(b"\x02", b"")
        start = token[:3]
        # https://stackoverflow.com/a/33206814
        # Colors
        if start == b"30m":
            self.parser.setTextColor(Qt.GlobalColor.black)
            self.parser.insertPlainText(token.replace(start, b"", 1).decode())
        elif start == b"31m":
            self.parser.setTextColor(PwndbgGuiConstants.RED)
            self.parser.insertPlainText(token.replace(start, b"", 1).decode())
        elif start == b"32m":
            self.parser.setTextColor(PwndbgGuiConstants.GREEN)
            self.parser.insertPlainText(token.replace(start, b"", 1).decode())
        elif start == b"33m":
            self.parser.setTextColor(PwndbgGuiConstants.YELLOW)
            self.parser.insertPlainText(token.replace(start, b"", 1).decode())
        elif start == b"34m":
            self.parser.setTextColor(PwndbgGuiConstants.LIGHT_BLUE)
            self.parser.insertPlainText(token.replace(start, b"", 1).decode())
        elif start == b"35m":
            self.parser.setTextColor(PwndbgGuiConstants.PURPLE)
            self.parser.insertPlainText(token.replace(start, b"", 1).decode())
        elif start == b"36m":
            self.parser.setTextColor(PwndbgGuiConstants.CYAN)
            self.parser.insertPlainText(token.replace(start, b"", 1).decode())
        elif start == b"37m":
            self.parser.setTextColor(Qt.GlobalColor.white)
            self.parser.insertPlainText(token.replace(start, b"", 1).decode())
        elif start.startswith(b"38"):
            # 256-bit color format: 38;5;<FG COLOR>m
            # RGB format: 38;2;<r>;<g>;<b>m
            start = token[:token.index(b"m")]
            args = start.split(b";")
            if args[1].isdigit() and int(args[1]) == 5:
                color = PwndbgGuiConstants.ANSI_COLOR_TO_RGB[int(args[2])]
                self.parser.setTextColor(QColor.fromRgb(color[0], color[1], color[2]))
            elif args[1].isdigit() and int(args[1]) == 2:
                r = int(args[2])
                g = int(args[3])
                b = int(args[4])
                self.parser.setTextColor(QColor.fromRgb(r, g, b, 255))
            # Add the "m" into the start for stripping
            start = token[:token.index(b"m")+1]
            self.parser.insertPlainText(token.replace(start, b"", 1).decode())
        elif start == b"39m":
            self.parser.setTextColor(Qt.GlobalColor.white)
            self.parser.insertPlainText(token.replace(start, b"").decode())
        elif start == b"91m":
            # Bright red
            self.parser.setTextColor(Qt.GlobalColor.red)
            self.parser.insertPlainText(token.replace(start, b"").decode())
        # Font
        elif start.startswith(b"0m"):
            self.reset_font()
            self.parser.insertPlainText(token[2:].decode())
        elif start.startswith(b"1m"):
            self.parser.setFontWeight(QFont.Weight.Bold)
            self.parser.insertPlainText(token[2:].decode())
        elif start.startswith(b"3m"):
            self.parser.setFontItalic(not self.parser.fontItalic())
            self.parser.insertPlainText(token[2:].decode())
        elif start.startswith(b"4m"):
            self.parser.setFontUnderline(not self.parser.fontUnderline())
            self.parser.insertPlainText(token[2:].decode())
        else:
            self.parser.insertPlainText(token.decode())
