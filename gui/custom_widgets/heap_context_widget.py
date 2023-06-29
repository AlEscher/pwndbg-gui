from typing import TYPE_CHECKING

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QWidget, QGroupBox, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit

# Prevent circular import error
if TYPE_CHECKING:
    from gui.pwndbg_gui import PwnDbgGui


class HeapContextWidget(QGroupBox):
    def __init__(self, parent: 'PwnDbgGui'):
        super().__init__(parent)
        # The "top" layout of the heap context widget
        self.context_layout = QVBoxLayout()
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setFlat(True)
        self.setTitle("Heap")
        self.setup_widget_layout()
        parent.ui.splitter.replaceWidget(1, self)

    def setup_widget_layout(self):
        try_malloc_layout = QHBoxLayout()
        try_malloc_layout.addWidget(QLabel("Try Malloc:"))
        try_malloc_input = QLineEdit()
        try_malloc_layout.addWidget(try_malloc_input)
        self.context_layout.addLayout(try_malloc_layout)
        try_free_layout = QHBoxLayout()
        try_free_layout.addWidget(QLabel("Try Free:"))
        try_free_input = QLineEdit()
        try_free_layout.addWidget(try_free_input)
        self.context_layout.addLayout(try_free_layout)
        self.setLayout(self.context_layout)
