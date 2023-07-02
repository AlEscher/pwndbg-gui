from PySide6.QtCore import Qt, QUrl
from PySide6.QtGui import QIcon, QDesktopServices
from PySide6.QtWidgets import QVBoxLayout, QDialog, QPushButton, QDialogButtonBox, QWidget

from gui.custom_widgets.context_text_edit import ContextTextEdit


class InfoMessageBox(QDialog):
    def __init__(self, parent: QWidget, title: str, content: str, url: str):
        super().__init__(parent)
        layout = QVBoxLayout()
        self.content = ContextTextEdit(self)
        self.content.add_content(content)
        self.content.setMinimumSize(800, 600)

        button_box = QDialogButtonBox(Qt.Orientation.Horizontal)
        ok_button = QPushButton("Ok")
        info_button = QPushButton("Info")

        ok_button.setIcon(QIcon.fromTheme("dialog-ok"))
        ok_button.clicked.connect(self.close)
        info_button.setIcon(QIcon.fromTheme("dialog-information"))
        info_button.clicked.connect(lambda: QDesktopServices.openUrl(QUrl(url)))

        button_box.addButton(ok_button, QDialogButtonBox.ButtonRole.AcceptRole)
        button_box.addButton(info_button, QDialogButtonBox.ButtonRole.HelpRole)

        layout.addWidget(self.content)
        layout.addWidget(button_box)

        self.setLayout(layout)
        self.setWindowTitle(title)
