# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'form.ui'
##
## Created by: Qt User Interface Compiler version 6.5.1
##
## WARNING! All changes made in this file will be lost when recompiling UI file!
################################################################################

from PySide6.QtCore import (QCoreApplication, QDate, QDateTime, QLocale,
    QMetaObject, QObject, QPoint, QRect,
    QSize, QTime, QUrl, Qt)
from PySide6.QtGui import (QBrush, QColor, QConicalGradient, QCursor,
    QFont, QFontDatabase, QGradient, QIcon,
    QImage, QKeySequence, QLinearGradient, QPainter,
    QPalette, QPixmap, QRadialGradient, QTransform)
from PySide6.QtWidgets import (QApplication, QListWidget, QListWidgetItem, QSizePolicy,
    QSplitter, QTextEdit, QWidget)

class Ui_PwnDbgGui(object):
    def setupUi(self, PwnDbgGui):
        if not PwnDbgGui.objectName():
            PwnDbgGui.setObjectName(u"PwnDbgGui")
        PwnDbgGui.resize(1367, 1037)
        self.top_splitter = QSplitter(PwnDbgGui)
        self.top_splitter.setObjectName(u"top_splitter")
        self.top_splitter.setGeometry(QRect(0, 10, 1361, 1021))
        self.top_splitter.setOrientation(Qt.Vertical)
        self.splitter_4 = QSplitter(self.top_splitter)
        self.splitter_4.setObjectName(u"splitter_4")
        self.splitter_4.setOrientation(Qt.Horizontal)
        self.code_splitter = QSplitter(self.splitter_4)
        self.code_splitter.setObjectName(u"code_splitter")
        self.code_splitter.setOrientation(Qt.Vertical)
        self.disasm = QTextEdit(self.code_splitter)
        self.disasm.setObjectName(u"disasm")
        self.disasm.setReadOnly(True)
        self.code_splitter.addWidget(self.disasm)
        self.code = QTextEdit(self.code_splitter)
        self.code.setObjectName(u"code")
        self.code.setReadOnly(True)
        self.code_splitter.addWidget(self.code)
        self.splitter_4.addWidget(self.code_splitter)
        self.splitter_3 = QSplitter(self.splitter_4)
        self.splitter_3.setObjectName(u"splitter_3")
        self.splitter_3.setOrientation(Qt.Vertical)
        self.regs = QTextEdit(self.splitter_3)
        self.regs.setObjectName(u"regs")
        self.splitter_3.addWidget(self.regs)
        self.backtrace = QTextEdit(self.splitter_3)
        self.backtrace.setObjectName(u"backtrace")
        self.backtrace.setReadOnly(True)
        self.splitter_3.addWidget(self.backtrace)
        self.splitter_4.addWidget(self.splitter_3)
        self.stack = QListWidget(self.splitter_4)
        self.stack.setObjectName(u"stack")
        self.splitter_4.addWidget(self.stack)
        self.top_splitter.addWidget(self.splitter_4)
        self.splitter = QSplitter(self.top_splitter)
        self.splitter.setObjectName(u"splitter")
        self.splitter.setOrientation(Qt.Horizontal)
        self.main = QTextEdit(self.splitter)
        self.main.setObjectName(u"main")
        self.splitter.addWidget(self.main)
        self.heap = QTextEdit(self.splitter)
        self.heap.setObjectName(u"heap")
        self.splitter.addWidget(self.heap)
        self.top_splitter.addWidget(self.splitter)

        self.retranslateUi(PwnDbgGui)

        QMetaObject.connectSlotsByName(PwnDbgGui)
    # setupUi

    def retranslateUi(self, PwnDbgGui):
        PwnDbgGui.setWindowTitle(QCoreApplication.translate("PwnDbgGui", u"PwnDbgGui", None))
    # retranslateUi

