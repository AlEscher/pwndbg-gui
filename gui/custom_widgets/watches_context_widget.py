import logging
from typing import TYPE_CHECKING, List

from PySide6.QtCore import Qt, Signal, Slot
from PySide6.QtWidgets import QGroupBox, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QSplitter, QWidget

from gui.custom_widgets.context_text_edit import ContextTextEdit
from gui.parser import ContextParser

# Prevent circular import error
if TYPE_CHECKING:
    from gui.pwndbg_gui import PwnDbgGui

logger = logging.getLogger(__file__)


class HDumpContextWidget(QGroupBox):
    # Execute "hexdump" in pwndbg and add watch in controller
    add_watch = Signal(str)
    # Delete watch in controller
    del_watch = Signal(str)

    def __init__(self, parent: 'PwnDbgGui'):
        super().__init__(parent)
        self.parser = ContextParser()
        # Currently watched addresses
        self.watches: List[str] = []
        # UI init
        self.watches_output: [ContextTextEdit] | None = None
        self.new_watch_input: QLineEdit | None = None
        # The watch context
        self.context_layout = QVBoxLayout()
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setFlat(True)
        self.setTitle("Watches")
        self.add_watch.connect(parent.gdb_handler.add_watch)
        self.del_watch.connect(parent.gdb_handler.del_watch)
        # Set up the interior layout of this widget
        self.setup_widget_layout()
        # Insert this widget into the UI
        parent.ui.splitter.replaceWidget(2, self)

    def setup_widget_layout(self):
        # The layout for the input mask (label and line edit) of the New Watch functionality
        new_watch_input_layout = QHBoxLayout()
        new_watch_input_label = QLabel("New Watch:")
        new_watch_input_label.setToolTip("Add an address to be watched every context update via 'hexdump'")
        new_watch_input_layout.addWidget(new_watch_input_label)
        self.new_watch_input = QLineEdit()
        self.new_watch_input.setToolTip("New address to watch")
        self.new_watch_input.returnPressed.connect(self.new_watch_submit)
        new_watch_input_layout.addWidget(self.new_watch_input)
        # Package the new_watch layout in a widget so that we can add it to the overall widget
        new_watch_widget = QWidget(self)
        new_watch_widget.setLayout(new_watch_input_layout)
        self.context_layout.addWidget(new_watch_widget)
        # Active Watches init with 1 for alignment
        self.watches_output = [ContextTextEdit(self)]
        self.context_layout.addWidget(self.watches_output[0])

        self.setLayout(self.context_layout)

    def new_watch_submit(self):
        """Callback for when the user presses Enter in the new_watch input mask"""
        param = self.new_watch_input.text()
        self.watches.append(param)
        self.add_watch.emit(param)
        self.new_watch_input.clear()

    def delete_watch_submit(self):
        """Callback for when the user presses Delete in the new_watch input mask"""
        param = self.new_watch_input.text()
        self.watches.remove(param)
        self.del_watch.emit(param)
        self.new_watch_input.clear()

    @Slot(bytes)
    def receive_hexdump_result(self, result: bytes):
        """Callback for receiving the result of the 'hexdump' command from the GDB reader"""
        self.watches_output[0].add_content(self.parser.to_html(result))
        pass
