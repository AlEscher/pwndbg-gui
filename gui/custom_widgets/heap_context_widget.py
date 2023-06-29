import logging
from typing import TYPE_CHECKING

from PySide6.QtCore import Qt, Signal, Slot
from PySide6.QtWidgets import QGroupBox, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit

from gui.custom_widgets.context_text_edit import ContextTextEdit
from gui.parser import ContextParser

# Prevent circular import error
if TYPE_CHECKING:
    from gui.pwndbg_gui import PwnDbgGui

logger = logging.getLogger(__file__)


class HeapContextWidget(QGroupBox):
    # Execute the "heap" command in pwndbg, the response will be signalled by the GDB reader
    get_heap_output = Signal()
    # Execute the "bins" command in pwndbg
    get_bins_output = Signal()
    # Execute "try_free" in pwndbg
    get_try_free = Signal(str)

    def __init__(self, parent: 'PwnDbgGui'):
        super().__init__(parent)
        self.parser = ContextParser()
        # The "top" layout of the heap context widget
        self.try_free_output: ContextTextEdit | None = None
        self.try_free_input: QLineEdit | None = None
        self.try_malloc_input: QLineEdit | None = None
        self.context_layout = QVBoxLayout()
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setFlat(True)
        self.setTitle("Heap")
        # The context uses these signals to interact with GDB and invoke commands. The results are received via Slots
        self.get_heap_output.connect(parent.gdb_handler.execute_heap_cmd)
        self.get_bins_output.connect(parent.gdb_handler.execute_bins_cmd)
        self.get_try_free.connect(parent.gdb_handler.execute_try_free)
        # Set up the interior layout of this widget
        self.setup_widget_layout()
        # Insert this widget into the UI
        parent.ui.splitter.replaceWidget(1, self)

    def setup_widget_layout(self):
        # The overall layout of the TryFree block, containing the input mask and output box
        try_free_layout = QVBoxLayout()
        # The layout for the input mask (label and line edit) of the Try Free functionality
        try_free_input_layout = QHBoxLayout()
        try_free_input_layout.addWidget(QLabel("Try Free:"))
        self.try_free_input = QLineEdit()
        self.try_free_input.returnPressed.connect(self.try_free_submit)
        try_free_input_layout.addWidget(self.try_free_input)
        try_free_layout.addLayout(try_free_input_layout)
        self.try_free_output = ContextTextEdit(self)
        try_free_layout.addWidget(self.try_free_output)
        self.context_layout.addLayout(try_free_layout)

        self.setLayout(self.context_layout)

    @Slot()
    def try_free_submit(self):
        param = self.try_free_input.text()
        self.get_try_free.emit(param)
        self.try_free_input.clear()

    @Slot(bytes)
    def receive_try_free_result(self, result: bytes):
        self.try_free_output.add_content(self.parser.to_html(result))
