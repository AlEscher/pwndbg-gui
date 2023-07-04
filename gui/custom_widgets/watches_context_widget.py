import logging
from typing import TYPE_CHECKING, List

from PySide6.QtCore import Qt, Signal, Slot, QParallelAnimationGroup, QPropertyAnimation, QAbstractAnimation, QSize
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QGroupBox, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QWidget, \
    QFrame, QScrollArea, QToolButton, QGridLayout, QSizePolicy, QBoxLayout, QSpinBox, QTextEdit, \
    QApplication

from gui.constants import PwndbgGuiConstants
from gui.custom_widgets.context_text_edit import ContextTextEdit
from gui.parser import ContextParser
from gui.tokens import ResponseToken

# Prevent circular import error
if TYPE_CHECKING:
    from gui.pwndbg_gui import PwnDbgGui

logger = logging.getLogger(__file__)


class Spoiler(QWidget):
    def __init__(self, content_layout: QBoxLayout, parent=None, title='', animationDuration=300):
        """
        References:
            # Adapted from c++ version
            http://stackoverflow.com/questions/32476006/how-to-make-an-expandable-collapsable-section-widget-in-qt
        """
        super(Spoiler, self).__init__(parent=parent)

        self.animationDuration = animationDuration
        self.toggleAnimation = QParallelAnimationGroup()
        self.contentArea = QScrollArea(parent=self)
        self.headerLine = QFrame(parent=self)
        self.toggleButton = QToolButton(parent=self)
        self.mainLayout = QGridLayout()

        toggle_button = self.toggleButton
        toggle_button.setStyleSheet("QToolButton { border: none; }")
        toggle_button.setToolButtonStyle(Qt.ToolButtonTextBesideIcon)
        toggle_button.setArrowType(Qt.RightArrow)
        toggle_button.setText(str(title))
        toggle_button.setCheckable(True)
        toggle_button.setChecked(False)

        header_line = self.headerLine
        header_line.setFrameShape(QFrame.Shape.HLine)
        header_line.setFrameShadow(QFrame.Shadow.Sunken)
        header_line.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Maximum)

        self.contentArea.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        # start out collapsed
        self.contentArea.setMaximumHeight(0)
        self.contentArea.setMinimumHeight(0)

        # let the entire widget grow and shrink with its content
        toggle_animation = self.toggleAnimation
        toggle_animation.addAnimation(QPropertyAnimation(self, b"minimumHeight"))
        toggle_animation.addAnimation(QPropertyAnimation(self, b"maximumHeight"))
        toggle_animation.addAnimation(QPropertyAnimation(self.contentArea, b"maximumHeight"))
        # don't waste space
        main_layout = self.mainLayout
        main_layout.setVerticalSpacing(0)
        main_layout.setContentsMargins(0, 0, 0, 0)
        row = 0
        main_layout.addWidget(self.toggleButton, row, 0, 1, 1, Qt.AlignLeft)
        main_layout.addWidget(self.headerLine, row, 2, 1, 1)
        row += 1
        main_layout.addWidget(self.contentArea, row, 0, 1, 3)
        self.setLayout(self.mainLayout)
        self.setContentLayout(content_layout)

        def start_animation(checked):
            arrow_type = Qt.DownArrow if checked else Qt.RightArrow
            direction = QAbstractAnimation.Forward if checked else QAbstractAnimation.Backward
            toggle_button.setArrowType(arrow_type)
            self.toggleAnimation.setDirection(direction)
            self.toggleAnimation.start()

        # Connect button and animation and finally toggle animation to be in the expanded state
        self.toggleButton.clicked.connect(start_animation)
        self.toggleButton.click()

    def setContentLayout(self, content_layout):
        self.contentArea.destroy()
        self.contentArea.setLayout(content_layout)
        self.update_content_height()

    def update_content_height(self):
        collapsed_height = self.sizeHint().height() - self.contentArea.maximumHeight()
        content_height = self.contentArea.layout().sizeHint().height()
        for i in range(self.toggleAnimation.animationCount() - 1):
            spoiler_animation = self.toggleAnimation.animationAt(i)
            spoiler_animation.setDuration(self.animationDuration)
            spoiler_animation.setStartValue(collapsed_height)
            spoiler_animation.setEndValue(collapsed_height + content_height)
        content_animation = self.toggleAnimation.animationAt(self.toggleAnimation.animationCount() - 1)
        content_animation.setDuration(self.animationDuration)
        content_animation.setStartValue(0)
        content_animation.setEndValue(content_height)

    def instant_update(self):
        # Lord have mercy on my soul for that I have sinned
        for i in range(self.toggleAnimation.animationCount() - 1):
            spoiler_animation = self.toggleAnimation.animationAt(i)
            spoiler_animation.setDuration(0)
        content_animation = self.toggleAnimation.animationAt(self.toggleAnimation.animationCount() - 1)
        content_animation.setDuration(0)
        self.toggleButton.click()
        self.toggleButton.click()
        for i in range(self.toggleAnimation.animationCount() - 1):
            spoiler_animation = self.toggleAnimation.animationAt(i)
            spoiler_animation.setDuration(self.animationDuration)
        content_animation = self.toggleAnimation.animationAt(self.toggleAnimation.animationCount() - 1)
        content_animation.setDuration(self.animationDuration)


class ActiveWatch:
    """Class that holds information for an active watch widget"""
    def __init__(self, address: str, index: int, spoiler: Spoiler, output: ContextTextEdit, numbytes: int):
        self.address = address
        self.index = index
        self.spoiler = spoiler
        self.output = output
        self.numbytes = numbytes


class HDumpContextWidget(QGroupBox):
    # Execute "hexdump" in pwndbg and add watch in controller
    add_watch = Signal(str, int)
    # Delete watch in controller
    del_watch = Signal(str)
    # Change num of watch lines in controller
    change_lines_watch = Signal(str, int)
    # Number of lines that the hexdump command will output for the Default number of bytes
    default_lines = (PwndbgGuiConstants.DEFAULT_WATCH_BYTES / 16 + 1)

    def __init__(self, parent: 'PwnDbgGui'):
        super().__init__(parent)
        self.parser = ContextParser()
        # Currently watched addresses as list of ActiveWatches
        self.watches: List[ActiveWatch] = []
        self.idx = 0
        # UI init
        self.active_watches_layout = QVBoxLayout()
        self.new_watch_input: QLineEdit | None = None
        # The watch context
        self.context_layout = QVBoxLayout()
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setFlat(True)
        self.setTitle("Watches")
        # Connect signals for gdb_handler communication
        self.add_watch.connect(parent.gdb_handler.add_watch)
        self.del_watch.connect(parent.gdb_handler.del_watch)
        self.change_lines_watch.connect(parent.gdb_handler.change_watch_lines)
        # Set up the interior layout of this widget
        self.setup_widget_layout()
        # Insert this widget into the UI
        parent.ui.splitter.replaceWidget(2, self)

    def setup_widget_layout(self):
        # The layout for the input mask (label and line edit) of the New Watch functionality
        new_watch_input_layout = QHBoxLayout()
        new_watch_input_label = QLabel("New Watch:", parent=self)
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

        # Wrapper for QScrollArea widget for added watches
        watches_scroll_area = QScrollArea(self)
        watches_scroll_area.setWidgetResizable(True)
        # Widget for the QScrollArea
        vertical_scroll_widget = QWidget(self)
        self.active_watches_layout = QVBoxLayout(vertical_scroll_widget)
        watches_scroll_area.setWidget(vertical_scroll_widget)
        self.context_layout.addWidget(watches_scroll_area)

        self.setLayout(self.context_layout)

    def setup_new_watch_widget(self, address: str):
        """
        Adds a new Spoiler widget to the active watches.
        :param address: address or expression to watch
        """
        # Setup inter Spoiler layout
        inter_spoiler_layout = QVBoxLayout()
        # First setup HBoxLayout for delete and lines
        watch_interact_layout = QHBoxLayout()
        watch_interact_layout.setAlignment(Qt.AlignmentFlag.AlignLeft)

        # Bytes Spinbox
        watch_lines_label = QLabel("Bytes:", parent=self)
        watch_interact_layout.addWidget(watch_lines_label)
        watch_lines_incrementor = QSpinBox()
        watch_lines_incrementor.setRange(1, 999)
        watch_lines_incrementor.setValue(PwndbgGuiConstants.DEFAULT_WATCH_BYTES)
        watch_lines_incrementor.valueChanged.connect(lambda value: self.change_lines_watch.emit(address, value))
        watch_lines_incrementor.setFixedHeight(QApplication.font().pointSize() * 2.5)
        watch_lines_incrementor.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        watch_interact_layout.addWidget(watch_lines_incrementor)

        # Delete button
        delete_watch_button = QToolButton()
        delete_watch_button.setIcon(QIcon.fromTheme("edit-delete"))
        delete_watch_button.setIconSize(QSize(QApplication.font().pointSize() * 2, QApplication.font().pointSize() * 2))
        delete_watch_button.setFixedSize(
            QSize(QApplication.font().pointSize() * 2.5, QApplication.font().pointSize() * 2.5))
        delete_watch_button.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonIconOnly)
        delete_watch_button.clicked.connect(lambda: self.delete_watch_submit(address))
        watch_interact_layout.addWidget(delete_watch_button)

        spoiler_interact_widget = QWidget(self)
        spoiler_interact_widget.setLayout(watch_interact_layout)
        inter_spoiler_layout.addWidget(spoiler_interact_widget)
        # Second setup hexdump output
        hexdump_output = ContextTextEdit(self)
        # Setting maximum height
        hexdump_output.set_maxheight_to_lines(self.default_lines)
        hexdump_output.setLineWrapMode(QTextEdit.LineWrapMode.NoWrap)
        inter_spoiler_layout.addWidget(hexdump_output)
        # Setup Spoiler
        spoiler = Spoiler(inter_spoiler_layout, parent=self, title=address)
        # Add watch to outer context
        self.watches.append(ActiveWatch(address, self.idx, spoiler, hexdump_output, PwndbgGuiConstants.DEFAULT_WATCH_BYTES))
        self.idx += 1
        self.active_watches_layout.insertWidget(0, spoiler)

    def find_watch_by_id(self, index: id) -> ActiveWatch:
        """
        Finds active ActiveWatch object by index.
        :param index: Index to search for.
        :return: ActiveWatch object with specified index.
        """
        found_watch = next((watch for watch in self.watches if watch.index == index), None)
        return found_watch

    def find_watch_by_address(self, address: str) -> ActiveWatch:
        """
            Finds active ActiveWatch object by address.
            :param address: Address to search for.
            :return: ActiveWatch object with specified address.
        """
        found_watch = next((watch for watch in self.watches if watch.address == address), None)
        return found_watch

    @Slot()
    def new_watch_submit(self):
        """Callback for when the user presses Enter in the new_watch input mask"""
        param = self.new_watch_input.text()
        if self.find_watch_by_address(param) is not None:
            self.new_watch_input.clear()
            return
        self.setup_new_watch_widget(param)
        self.add_watch.emit(param, self.find_watch_by_address(param).index)
        self.new_watch_input.clear()

    @Slot(str)
    def delete_watch_submit(self, address: str):
        """Callback for when the user presses Delete in one of the watch spoilers
        :param address: Address to delete
        """
        watch = self.find_watch_by_address(address)
        self.context_layout.removeWidget(watch.spoiler)
        watch.spoiler.deleteLater()
        self.watches.remove(watch)
        self.del_watch.emit(address)

    @Slot(int, bytes)
    def receive_hexdump_result(self, token: int, result: bytes):
        """Slot for receiving the result of the 'hexdump' command from the GDB reader
        :param token: Token that identifies the answer from pygdbmi.
        :param result: Content to update the watch with.
        """
        index = token - ResponseToken.GUI_WATCHES_HEXDUMP
        watch = self.find_watch_by_id(index)
        if watch is not None:
            # First trim the first column if necessary
            lines = result.split(b'\n')
            non_empty_lines = [line for line in lines if line]
            # Throwaway the first column if it is an offset column
            trimmed_lines = [line.split(b' ', 1)[1] if line.startswith(b"+0") else line for line in non_empty_lines]
            content = b'\n'.join(trimmed_lines)

            # Second add content to the watch and reset scrollbars
            watch.output.add_content(self.parser.to_html(content))
            watch.output.verticalScrollBar().setValue(0)
            watch.output.horizontalScrollBar().setValue(0)

            # Adapt output size if content now is less than before
            line_count = len(result.split(b"\n"))
            if line_count < self.default_lines:
                watch.output.set_maxheight_to_lines(line_count)
            else:
                watch.output.set_maxheight_to_lines(self.default_lines)

            # Last update spoiler size
            watch.spoiler.update_content_height()
            watch.spoiler.instant_update()
