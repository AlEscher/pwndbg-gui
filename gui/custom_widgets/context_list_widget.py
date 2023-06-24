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
        for line in lines:
            QListWidgetItem(line, self)

