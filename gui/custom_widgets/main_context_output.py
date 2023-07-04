from PySide6.QtGui import QTextCursor
from PySide6.QtWidgets import QWidget

from gui.custom_widgets.context_text_edit import ContextTextEdit


class MainContextOutput(ContextTextEdit):
    def __init__(self, parent: QWidget):
        super().__init__(parent)
        self.setObjectName("main")

    def add_content(self, content: str):
        """Appends content instead of replacing it like other normal ContextTextEdit widgets"""
        # Prevent selected text from being overwritten
        cursor = self.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.End, QTextCursor.MoveMode.MoveAnchor)
        self.setTextCursor(cursor)
        self.insertHtml(content)
        # Scroll to the bottom
        self.ensureCursorVisible()
