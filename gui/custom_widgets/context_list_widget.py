import logging
import re
from typing import TYPE_CHECKING

from PySide6.QtCore import Qt, Signal, Slot, QKeyCombination
from PySide6.QtGui import QIcon, QKeySequence, QKeyEvent
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
        self.setResizeMode(QListWidget.ResizeMode.Adjust)
        self.context_menu = QMenu(self)
        self.context_shortcuts = {"copy_address": QKeyCombination(Qt.KeyboardModifier.ControlModifier | Qt.KeyboardModifier.ShiftModifier | Qt.Key.Key_C),
                                  "copy_value": QKeyCombination(Qt.KeyboardModifier.ControlModifier | Qt.KeyboardModifier.ShiftModifier | Qt.Key.Key_V),
                                  "xinfo_address": QKeyCombination(Qt.KeyboardModifier.ControlModifier | Qt.Key.Key_X),
                                  "xinfo_value": QKeyCombination(Qt.KeyboardModifier.ControlModifier | Qt.KeyboardModifier.ShiftModifier | Qt.Key.Key_X)}
        self.setup_context_menu()

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

    def setup_context_menu(self):
        # Copy the address data, for a stack this is the stack address, for a register this is the register's content
        copy_addr_action = self.context_menu.addAction("Copy Address")
        copy_addr_action.setIcon(QIcon.fromTheme("edit-copy"))
        # Shortcuts don't work for some reason, we still set them to get the text in the context menu
        copy_addr_action.setShortcut(self.context_shortcuts["copy_address"])
        copy_addr_action.triggered.connect(self.copy_address)
        # Copy the value data, for a stack this is the value that the stack address points to,
        # for a register this is the value that the address points to if one exists
        copy_val_action = self.context_menu.addAction("Copy Value")
        copy_val_action.setIcon(QIcon.fromTheme("edit-copy"))
        copy_val_action.setShortcut(self.context_shortcuts["copy_value"])
        copy_val_action.triggered.connect(self.copy_value)
        # Show a dialog with offset information about the address entry
        offset_address_action = self.context_menu.addAction("Show Address Offsets")
        offset_address_action.setIcon(QIcon.fromTheme("system-search"))
        offset_address_action.setShortcut(self.context_shortcuts["xinfo_address"])
        offset_address_action.triggered.connect(self.xinfo_address)
        # Show a dialog with offset information about the value entry
        offset_value_action = self.context_menu.addAction("Show Value Offsets")
        offset_value_action.setIcon(QIcon.fromTheme("system-search"))
        offset_value_action.setShortcut(self.context_shortcuts["xinfo_value"])
        offset_value_action.triggered.connect(self.xinfo_value)

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

    def keyPressEvent(self, event: QKeyEvent):
        """Event handler for any key presses on this widget"""
        if event.matches(QKeySequence.StandardKey.Copy):
            # When the user presses Ctrl+C, we copy the selected stack line into his clipboard
            selected_items = self.selectedItems()
            if selected_items:
                item = selected_items[0]
                data = self.parser.from_html(item.text())
                if data:
                    QApplication.clipboard().setText(data)
                return
        # We have to do this garbage here manually because Qt Shortcuts don't work for the context menu actions
        elif event.keyCombination().toCombined() == self.context_shortcuts["copy_address"].toCombined():
            self.copy_address()
            return
        elif event.keyCombination().toCombined() == self.context_shortcuts["copy_value"].toCombined():
            self.copy_value()
            return
        elif event.keyCombination().toCombined() == self.context_shortcuts["xinfo_address"].toCombined():
            self.xinfo_address()
            return
        elif event.keyCombination().toCombined() == self.context_shortcuts["xinfo_value"].toCombined():
            self.xinfo_value()
            return

        super().keyPressEvent(event)

    @Slot()
    def copy_value(self):
        self.set_data_to_clipboard(self.selectedItems()[0], ContextDataRole.VALUE)

    @Slot()
    def copy_address(self):
        self.set_data_to_clipboard(self.selectedItems()[0], ContextDataRole.ADDRESS)

    @Slot()
    def xinfo_address(self):
        self.execute_xinfo.emit(str(self.selectedItems()[0].data(ContextDataRole.ADDRESS)))

    @Slot()
    def xinfo_value(self):
        self.execute_xinfo.emit(str(self.selectedItems()[0].data(ContextDataRole.VALUE)))

    def contextMenuEvent(self, event):
        selected_items = self.selectedItems()
        if selected_items is None or len(selected_items) == 0:
            super().contextMenuEvent(event)
            return
        self.context_menu.exec(event.globalPos())

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

    def resizeEvent(self, resizeEvent):
        self.reset()
        super().resizeEvent(resizeEvent)
