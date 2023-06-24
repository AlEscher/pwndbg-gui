from PySide6.QtCore import QRectF, QSize
from PySide6.QtGui import QTextDocument, QAbstractTextDocumentLayout
from PySide6.QtWidgets import QStyledItemDelegate, QStyleOptionViewItem, QStyle


# https://stackoverflow.com/a/66091713
class HTMLDelegate(QStyledItemDelegate):
    def __init__(self):
        super().__init__()
        # probably better not to create new QTextDocuments every ms
        self.doc = QTextDocument()

    def paint(self, painter, option, index):
        options = QStyleOptionViewItem(option)
        self.initStyleOption(options, index)
        painter.save()
        self.doc.setTextWidth(options.rect.width())
        self.doc.setHtml(options.text)
        self.doc.setDefaultFont(options.font)
        options.text = ''
        options.widget.style().drawControl(QStyle.ControlElement.CE_ItemViewItem, options, painter)
        painter.translate(options.rect.left(), options.rect.top())
        clip = QRectF(0, 0, options.rect.width(), options.rect.height())
        painter.setClipRect(clip)
        ctx = QAbstractTextDocumentLayout.PaintContext()
        ctx.clip = clip
        self.doc.documentLayout().draw(painter, ctx)
        painter.restore()

    def sizeHint(self, option, index):
        options = QStyleOptionViewItem(option)
        self.initStyleOption(option, index)
        self.doc.setHtml(option.text)
        self.doc.setTextWidth(option.rect.width())
        return QSize(self.doc.idealWidth(), self.doc.size().height())
