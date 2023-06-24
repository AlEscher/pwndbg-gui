from typing import TYPE_CHECKING
import re

from PySide6.QtWidgets import QListWidget, QListWidgetItem

# Prevent circular import error
if TYPE_CHECKING:
    from gui.gui import PwnDbgGui


def delete_first_html_tag(string):
    pattern = r"<[^>]+>"  # Regular expression pattern to match HTML tags
    return re.sub(pattern, "", string, count=1)


def delete_last_html_tag(string):
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


class ContextListWidget(QListWidget):
    def __init__(self, parent: 'PwnDbgGui', ):
        super().__init__(parent)

    def add_content(self, content: str):
        self.clear()
        lines = content.splitlines()
        # Remove unneeded lines containing only HTML, as "content" will be a full HTML document returned by the parser
        body_start = lines.index(next(line for line in lines if "<body" in line))
        for line in lines[body_start + 1:]:
            QListWidgetItem(delete_first_html_tag(delete_last_html_tag(line)), self)
