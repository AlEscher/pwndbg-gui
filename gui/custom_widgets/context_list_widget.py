import logging
import re
from typing import TYPE_CHECKING

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QListWidget, QListWidgetItem, QApplication, QMenu, QSplitter, QGroupBox, QVBoxLayout

from gui.context_data_role import ContextDataRole
from gui.parser import ContextParser

# Prevent circular import error
if TYPE_CHECKING:
    from gui.pwndbg_gui import PwnDbgGui

logger = logging.getLogger(__file__)


class ContextListWidget(QListWidget):
    execute_xinfo = Signal(str)
    value_xinfo = Signal(str)

    def __init__(self, parent: 'PwnDbgGui', title: str, splitter: QSplitter, index: int):
        super().__init__(parent)
        self.parser = ContextParser()
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

    def add_content(self, content: str):
        self.clear()
        lines = content.splitlines()
        # Remove unneeded lines containing only HTML, as "content" will be a full HTML document returned by the parser
        body_start = lines.index(next(line for line in lines if "<body" in line))
        for line in lines[body_start + 1:]:
            # Remove <p...></p> tag
            cleaned = self.delete_first_html_tag(self.delete_last_html_tag(line))
            item = QListWidgetItem(self)
            item.setData(Qt.ItemDataRole.DisplayRole, cleaned)
            plain_text = self.parser.from_html(line)
            address, value = self.find_hex_values(plain_text)
            item.setData(ContextDataRole.ADDRESS, address)
            item.setData(ContextDataRole.VALUE, value)

    def keyPressEvent(self, event):
        """Event handler for any key presses on this widget"""
        if event.modifiers() == Qt.KeyboardModifier.ControlModifier and event.key() == Qt.Key.Key_C:
            # When the user presses Ctrl+C, we copy the selected stack line into his clipboard
            selected_items = self.selectedItems()
            if selected_items:
                item = selected_items[0]
                data = self.parser.from_html(item.text())
                if data:
                    QApplication.clipboard().setText(data)
                return
        super().keyPressEvent(event)

    def contextMenuEvent(self, event):
        selected_items = self.selectedItems()
        if selected_items is None or len(selected_items) == 0:
            super().contextMenuEvent(event)
            return
        menu = QMenu(self)
        # Copy the address data, for a stack this is the stack address, for a register this is the register's content
        copy_addr_action = menu.addAction("Copy Address")
        # Copy the value data, for a stack this is the value that the stack address points to,
        # for a register this is the value that the address points to if one exists
        copy_val_action = menu.addAction("Copy Value")
        # Show a dialog with offset information about the address entry
        offset_address_action = menu.addAction("Show Address Offsets")
        # Show a dialog with offset information about the value entry
        offset_value_action = menu.addAction("Show Value Offsets")
        action = menu.exec(event.globalPos())
        item = selected_items[0]
        if action == copy_addr_action:
            self.set_data_to_clipboard(item, ContextDataRole.ADDRESS)
        elif action == copy_val_action:
            self.set_data_to_clipboard(item, ContextDataRole.VALUE)
        elif action == offset_address_action and item.data(ContextDataRole.ADDRESS) is not None:
            self.execute_xinfo.emit(str(item.data(ContextDataRole.ADDRESS)))
        elif action == offset_value_action and item.data(ContextDataRole.VALUE) is not None:
            self.execute_xinfo.emit(str(item.data(ContextDataRole.VALUE)))

    def delete_first_html_tag(self, string: str):
        pattern = r"<[^>]+>"  # Regular expression pattern to match HTML tags
        return re.sub(pattern, "", string, count=1)

    def delete_last_html_tag(self, string: str):
        # Find the last closing HTML tag
        pattern = r'</[^>]+>$'
        match = re.search(pattern, string)

        if match:
            last_tag = match.group()
            # Remove the last closing HTML tag
            modified_string = string.replace(last_tag, '')
            return modified_string
        else:
            return string  # No closing HTML tag found

    def find_hex_values(self, line: str):
        pattern = re.compile(r"0x[0-9a-fA-F]+", re.UNICODE)
        # Filter out empty matches
        hex_values = [match for match in pattern.findall(line) if match]
        first_value = ""
        second_value = ""
        if len(hex_values) > 0:
            first_value = hex_values[0]
        if len(hex_values) > 1:
            second_value = hex_values[1]
        return first_value, second_value

    def set_data_to_clipboard(self, item: QListWidgetItem, role: ContextDataRole):
        data = item.data(role)
        if data is not None:
            QApplication.clipboard().setText(data)
