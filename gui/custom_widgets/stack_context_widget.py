from typing import TYPE_CHECKING

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QGroupBox, QVBoxLayout, QSplitter, QHBoxLayout, QLabel, QSpinBox

from gui.custom_widgets.context_list_widget import ContextListWidget
from gui.html_style_delegate import HTMLDelegate

# Prevent circular import error
if TYPE_CHECKING:
    from gui.pwndbg_gui import PwnDbgGui


class StackContextWidget(ContextListWidget):
    def __init__(self, parent: 'PwnDbgGui', title: str, splitter: QSplitter, index: int):
        super().__init__(parent, title, splitter, index)
        self.setObjectName("stack")
        self.setItemDelegate(HTMLDelegate())

    def setup_widget_layout(self, parent: 'PwnDbgGui', title: str, splitter: QSplitter, index: int):
        # GroupBox needs to have parent before being added to splitter (see SO below)
        context_box = QGroupBox(title, parent)
        context_box.setAlignment(Qt.AlignmentFlag.AlignCenter)
        context_box.setFlat(True)
        context_layout = QVBoxLayout()
        self.add_stack_header(context_layout)
        context_layout.addWidget(self)
        context_box.setLayout(context_layout)
        splitter.replaceWidget(index, context_box)
        # https://stackoverflow.com/a/66067630
        context_box.show()

    def add_stack_header(self, layout: QVBoxLayout):
        # Add a stack count inc-/decrementor
        self.stack_lines_incrementor = QSpinBox()
        header_layout = QHBoxLayout()
        header_layout.setAlignment(Qt.AlignmentFlag.AlignLeft)
        stack_lines_label = QLabel("Stack Lines:")
        header_layout.addWidget(stack_lines_label)
        self.stack_lines_incrementor.setRange(1, 999)
        self.stack_lines_incrementor.setValue(8)
        header_layout.addWidget(self.stack_lines_incrementor)
        layout.addLayout(header_layout)
