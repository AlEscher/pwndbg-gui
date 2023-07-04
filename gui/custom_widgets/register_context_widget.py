from typing import TYPE_CHECKING

from PySide6.QtCore import Qt, Slot
from PySide6.QtWidgets import QSplitter, QListWidgetItem

from gui.context_data_role import ContextDataRole
from gui.custom_widgets.context_list_widget import ContextListWidget
from gui.html_style_delegate import HTMLDelegate

# Prevent circular import error
if TYPE_CHECKING:
    from gui.pwndbg_gui import PwnDbgGui


class RegisterContextWidget(ContextListWidget):
    def __init__(self, parent: 'PwnDbgGui', title: str, splitter: QSplitter, index: int):
        super().__init__(parent, title, splitter, index)
        self.setObjectName("regs")
        self.setItemDelegate(HTMLDelegate())

    @Slot(bytes)
    def receive_fs_base(self, content: bytes):
        """Callback to receive the hex value of the fs register"""
        cleaned = self.parser.to_html(b" \x1b[1mFS \x1b[0m \x1b[35m" + content + b"\x1b[0m").splitlines()
        # Remove unneeded lines containing only HTML, as "content" will be a full HTML document returned by the parser
        body_start = cleaned.index(next(line for line in cleaned if "<body" in line))
        cleaned_line = self.delete_first_html_tag(self.delete_last_html_tag(cleaned[body_start + 1]))
        item = QListWidgetItem(self)
        item.setData(Qt.ItemDataRole.DisplayRole, cleaned_line)
        item.setData(ContextDataRole.ADDRESS, content.decode().strip())
        item.setData(ContextDataRole.VALUE, content.decode().strip())
