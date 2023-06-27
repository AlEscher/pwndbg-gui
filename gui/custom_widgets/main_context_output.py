from PySide6.QtWidgets import QWidget

from gui.custom_widgets.context_text_edit import ContextTextEdit


class MainContextOutput(ContextTextEdit):
    def __init__(self, parent: QWidget):
        super().__init__(parent)
        self.setObjectName("main")

    def add_content(self, content: str):
        """Appends content instead of replacing it like other normal ContextTextEdit widgets"""
        super().add_content(self.toHtml() + content)
