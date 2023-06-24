from typing import TYPE_CHECKING

from PySide6.QtGui import QTextCursor
from PySide6.QtWidgets import QTextEdit

# Prevent circular import error
if TYPE_CHECKING:
    from gui.gui import PwnDbgGui


class ContextTextEdit(QTextEdit):
    def __init__(self, parent: 'PwnDbgGui', ):
        super().__init__(parent)
        self.setReadOnly(True)

    def add_content(self, content: str):
        self.setHtml(content)
        cursor = self.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.End, QTextCursor.MoveMode.MoveAnchor)
        self.setTextCursor(cursor)
