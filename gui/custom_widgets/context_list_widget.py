from typing import TYPE_CHECKING

from PySide6.QtWidgets import QListWidget, QListWidgetItem

# Prevent circular import error
if TYPE_CHECKING:
    from gui.gui import PwnDbgGui


class ContextListWidget(QListWidget):
    def __init__(self, parent: 'PwnDbgGui', ):
        super().__init__(parent)

    def add_content(self, content: str):
        lines = content.splitlines()
        # Remove unneeded lines containing only HTML, as "content" will be a full HTML document returned by the parser
        body_start = lines.index(next(line for line in lines if "<body" in line))
        for line in lines[body_start+1:]:
            QListWidgetItem(line, self)

