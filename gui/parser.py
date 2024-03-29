from PySide6.QtCore import Qt
from PySide6.QtGui import QFont, QColor
from PySide6.QtWidgets import QTextEdit

from gui.constants import PwndbgGuiConstants

import logging

logger = logging.getLogger(__file__)


class ContextParser:
    """Parses raw output from gdb/pwndbg containing ASCII control characters into equivalent HTML code"""

    def __init__(self):
        # Misuse QTextEdit as a HTML parser
        self.parser = QTextEdit()

    def reset(self):
        """
        Reset the internal parser
        """
        self.parser.clear()
        self.reset_font()

    def parse(self, raw_output: bytes, remove_headers=False):
        """
        Parse program output containing ASCII control characters
        :param raw_output: The output as received from e.g. pwndbg
        :param remove_headers: Whether to remove the header, e.g. for "context" commands
        """
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
        """
        Parses output containing ASCII control characters into equivalent HTML code
        :param raw_output: The output as received from e.g. pwndbg
        :param remove_headers: Whether to remove the header, e.g. for "context" commands
        :return:
        """
        self.parse(raw_output, remove_headers)
        return self.parser.toHtml()

    def from_html(self, html: str):
        """
        Takes HTML and returns the plain text content
        :param html: The valid HTML representation of an output
        :return:
        """
        self.reset()
        self.parser.setHtml(html)
        return self.parser.toPlainText()

    def reset_font(self):
        self.parser.setFontWeight(QFont.Weight.Normal)
        self.parser.setTextColor(Qt.GlobalColor.white)
        self.parser.setFontUnderline(False)
        self.parser.setFontItalic(False)

    def parse_ascii_control(self, token: bytes):
        """
        Parse a single token, if it is an ASCII control character emulate it (e.g. change text color) and
        otherwise add any normal plain text to the parser's document
        :param token: A single token
        """
        # Remove weird bytes, e.g. in \x01\x1b[31m\x1b[1m\x02pwndbg> \x01\x1b[0m\x1b[31m\x1b[0m\x02
        token = token.replace(b"\x01", b"").replace(b"\x02", b"")
        start = token[:3]
        # https://stackoverflow.com/a/33206814
        # Colors
        if start == b"30m":
            self.parser.setTextColor(Qt.GlobalColor.black)
            self.insert_token(token.replace(start, b"", 1))
        elif start == b"31m":
            self.parser.setTextColor(PwndbgGuiConstants.RED)
            self.insert_token(token.replace(start, b"", 1))
        elif start == b"32m":
            self.parser.setTextColor(PwndbgGuiConstants.GREEN)
            self.insert_token(token.replace(start, b"", 1))
        elif start == b"33m":
            self.parser.setTextColor(PwndbgGuiConstants.YELLOW)
            self.insert_token(token.replace(start, b"", 1))
        elif start == b"34m":
            self.parser.setTextColor(PwndbgGuiConstants.LIGHT_BLUE)
            self.insert_token(token.replace(start, b"", 1))
        elif start == b"35m":
            self.parser.setTextColor(PwndbgGuiConstants.PURPLE)
            self.insert_token(token.replace(start, b"", 1))
        elif start == b"36m":
            self.parser.setTextColor(PwndbgGuiConstants.CYAN)
            self.insert_token(token.replace(start, b"", 1))
        elif start == b"37m":
            self.parser.setTextColor(Qt.GlobalColor.white)
            self.insert_token(token.replace(start, b"", 1))
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
            start = token[:token.index(b"m") + 1]
            self.insert_token(token.replace(start, b"", 1))
        elif start == b"39m":
            self.parser.setTextColor(Qt.GlobalColor.white)
            self.insert_token(token.replace(start, b""))
        elif start == b"91m":
            # Bright red
            self.parser.setTextColor(Qt.GlobalColor.red)
            self.insert_token(token.replace(start, b""))
        # Font
        elif start.startswith(b"0m"):
            self.reset_font()
            self.insert_token(token[2:])
        elif start.startswith(b"1m"):
            self.parser.setFontWeight(QFont.Weight.Bold)
            self.insert_token(token[2:])
        elif start.startswith(b"3m"):
            self.parser.setFontItalic(not self.parser.fontItalic())
            self.insert_token(token[2:])
        elif start.startswith(b"4m"):
            self.parser.setFontUnderline(not self.parser.fontUnderline())
            self.insert_token(token[2:])
        else:
           self.insert_token(token)

    def insert_token(self, token: bytes):
        try:
            self.parser.insertPlainText(token.decode())
        except UnicodeDecodeError:
            self.parser.insertPlainText(repr(token))
