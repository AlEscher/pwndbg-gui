import logging

from PySide6.QtGui import QTextCursor
from PySide6.QtWidgets import QTextEdit, QWidget

logger = logging.getLogger(__file__)


class ContextTextEdit(QTextEdit):
    def __init__(self, parent: QWidget):
        super().__init__(parent)
        self.setReadOnly(True)

    def add_content(self, content: str):
        self.setHtml(content)
        cursor = self.textCursor()
        # Move cursor to the end, so that the subsequent ensureCursorVisible will scroll UP
        cursor.movePosition(QTextCursor.MoveOperation.End, QTextCursor.MoveMode.MoveAnchor)
        self.setTextCursor(cursor)
        # Scroll so that the current line in "code" and "disasm" contexts is in view
        self.find_and_set_cursor("►")

    def find_and_set_cursor(self, character: str):
        cursor = self.textCursor()
        content = self.toPlainText()
        char_index = content.find(character)
        if char_index != -1:
            cursor.setPosition(char_index)
            self.setTextCursor(cursor)
            self.ensureCursorVisible()

    def set_maxheight_to_lines(self, lines: int):
        font_metrics = self.fontMetrics()
        line_height = font_metrics.lineSpacing()
        extra_height = font_metrics.leading()
        self.setMaximumHeight((line_height + extra_height) * lines)
