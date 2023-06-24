from typing import List

from PySide6.QtCore import Qt
from PySide6.QtGui import QFont, QColor
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
        elif start.startswith(b"38"):
            # 256-bit color format: 38;5;<FG COLOR>m
            # RGB format: 38;2;<r>;<g>;<b>m
            start = token[:token.index(b"m")]
            args = start.split(b";")
            if args[1].isdigit() and int(args[1]) == 5:
                color = convert_8bit_to_32bit(int(args[2]))
                self.parser.setTextColor(QColor.fromRgba(color))
            elif args[1].isdigit() and int(args[1]) == 2:
                r = int(args[2])
                g = int(args[3])
                b = int(args[4])
                self.parser.setTextColor(QColor.fromRgb(r, g, b, 255))
            # Add the "m" into the start for stripping
            start = token[:token.index(b"m")+1]
            self.parser.insertPlainText(token.strip(start).decode())
        elif start == b"91m":
            # TODO, Ignore for now
            pass
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


def convert_8bit_to_32bit(rgb_8bit):
    # Extracting the 8-bit color components
    red = (rgb_8bit >> 5) & 0b111  # 3 bits for red
    green = (rgb_8bit >> 2) & 0b111  # 3 bits for green
    blue = rgb_8bit & 0b11  # 2 bits for blue

    # Expanding the color values to 32-bit
    red_32bit = (red << 5) | (red << 2) | (red >> 1)
    green_32bit = (green << 5) | (green << 2) | (green >> 1)
    blue_32bit = (blue << 6) | (blue << 4) | (blue << 2) | blue
    alpha_32bit = 0xFF  # Alpha value set to maximum (255)

    # Combining the 32-bit color components
    rgb_32bit = (alpha_32bit << 24) | (red_32bit << 16) | (green_32bit << 8) | blue_32bit

    return rgb_32bit
