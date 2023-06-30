import logging
from typing import TYPE_CHECKING

from PySide6.QtCore import Qt, Signal, Slot
from PySide6.QtWidgets import QGroupBox, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QSplitter, QWidget

from gui.custom_widgets.context_text_edit import ContextTextEdit
from gui.parser import ContextParser

# Prevent circular import error
if TYPE_CHECKING:
    from gui.pwndbg_gui import PwnDbgGui

logger = logging.getLogger(__file__)


class HeapContextWidget(QGroupBox):
    # Execute "try_free" in pwndbg
    get_try_free = Signal(str)

    def __init__(self, parent: 'PwnDbgGui'):
        super().__init__(parent)
        self.parser = ContextParser()
        self.bins_output: ContextTextEdit | None = None
        self.heap_output: ContextTextEdit | None = None
        self.try_free_output: ContextTextEdit | None = None
        self.try_free_input: QLineEdit | None = None
        # The "top" layout of the whole heap context widget
        self.context_layout = QVBoxLayout()
        self.context_splitter = QSplitter()
        self.context_splitter.setOrientation(Qt.Orientation.Vertical)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setFlat(True)
        self.setTitle("Heap")
        self.get_try_free.connect(parent.gdb_handler.execute_try_free)
        # Set up the interior layout of this widget
        self.setup_widget_layout()
        # Insert this widget into the UI
        parent.ui.splitter.replaceWidget(1, self)

    def setup_widget_layout(self):
        output_splitter = QSplitter()
        output_splitter.setOrientation(Qt.Orientation.Horizontal)

        self.heap_output = ContextTextEdit(self)
        output_splitter.addWidget(self.heap_output)
        self.bins_output = ContextTextEdit(self)
        output_splitter.addWidget(self.bins_output)
        self.context_splitter.addWidget(output_splitter)

        # The overall element of the TryFree block, containing the input mask and output box
        try_free_layout = QVBoxLayout()
        # The layout for the input mask (label and line edit) of the Try Free functionality
        try_free_input_layout = QHBoxLayout()
        try_free_label = QLabel("Try Free:")
        try_free_label.setToolTip("Simulate a free() call on a heap pointer")
        try_free_input_layout.addWidget(try_free_label)
        self.try_free_input = QLineEdit()
        self.try_free_input.setToolTip("Simulate a free() call on a heap pointer")
        self.try_free_input.returnPressed.connect(self.try_free_submit)
        try_free_input_layout.addWidget(self.try_free_input)
        try_free_layout.addLayout(try_free_input_layout)
        self.try_free_output = ContextTextEdit(self)
        try_free_layout.addWidget(self.try_free_output)
        # Package the try_free layout in a widget so that we can add it to the splitter
        try_free_widget = QWidget(self)
        try_free_widget.setLayout(try_free_layout)
        self.context_splitter.addWidget(try_free_widget)

        self.context_layout.addWidget(self.context_splitter)
        self.setLayout(self.context_layout)

    @Slot()
    def try_free_submit(self):
        """Callback for when the user presses Enter in the try_free input mask"""
        param = self.try_free_input.text()
        self.get_try_free.emit(param)
        self.try_free_input.clear()

    @Slot(bytes)
    def receive_try_free_result(self, result: bytes):
        """Callback for receiving the result of the 'try_free' command from the GDB reader"""
        self.try_free_output.add_content(self.parser.to_html(result))

    @Slot(bytes)
    def receive_heap_result(self, result: bytes):
        """Callback for receiving the result of the 'heap' command from the GDB reader"""
        self.heap_output.add_content(self.parser.to_html(result))

    @Slot(bytes)
    def receive_bins_result(self, result: bytes):
        """Callback for receiving the result of the 'bins' command from the GDB reader"""
        self.bins_output.add_content(self.parser.to_html(result))
