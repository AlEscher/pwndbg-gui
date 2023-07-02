from typing import TYPE_CHECKING

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QSplitter, QGroupBox, QVBoxLayout

from gui.custom_widgets.context_text_edit import ContextTextEdit

# Prevent circular import error
if TYPE_CHECKING:
    from gui.pwndbg_gui import PwnDbgGui


class ContextTextWidget(ContextTextEdit):
    """Wrap the ContextTextEdit in a Groupbox with a header"""
    def __init__(self, parent: 'PwnDbgGui', title: str, splitter: QSplitter, index: int):
        super().__init__(parent)
        self.setReadOnly(True)
        self.setup_widget_layout(parent, title, splitter, index)

    def setup_widget_layout(self, parent: 'PwnDbgGui', title: str, splitter: QSplitter, index: int):
        # GroupBox needs to have parent before being added to splitter (see SO below)
        context_box = QGroupBox(title, parent)
        context_box.setAlignment(Qt.AlignmentFlag.AlignCenter)
        context_box.setFlat(True)
        context_layout = QVBoxLayout()
        context_layout.addWidget(self)
        context_box.setLayout(context_layout)
        splitter.replaceWidget(index, context_box)
        # https://stackoverflow.com/a/66067630
        context_box.show()
