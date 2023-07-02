from typing import TYPE_CHECKING

from PySide6.QtWidgets import QSplitter

from gui.custom_widgets.context_text_widget import ContextTextWidget

# Prevent circular import error
if TYPE_CHECKING:
    from gui.pwndbg_gui import PwnDbgGui


class CodeContextWidget(ContextTextWidget):
    def __init__(self, parent: 'PwnDbgGui', title: str, splitter: QSplitter, index: int):
        super().__init__(parent, title, splitter, index)
        self.setObjectName("code")
        self.setup_widget_layout(parent, title, splitter, index)
