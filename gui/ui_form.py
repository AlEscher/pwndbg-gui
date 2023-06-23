# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'form.ui'
##
## Created by: Qt User Interface Compiler version 6.5.0
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
from PySide6.QtWidgets import (QApplication, QSizePolicy, QSplitter, QTextEdit,
    QWidget)

class Ui_PwnDbgGui(object):
    def setupUi(self, PwnDbgGui):
        if not PwnDbgGui.objectName():
            PwnDbgGui.setObjectName(u"PwnDbgGui")
        PwnDbgGui.resize(1367, 1037)
        self.splitter_5 = QSplitter(PwnDbgGui)
        self.splitter_5.setObjectName(u"splitter_5")
        self.splitter_5.setGeometry(QRect(0, 10, 1361, 1021))
        self.splitter_5.setOrientation(Qt.Vertical)
        self.splitter_4 = QSplitter(self.splitter_5)
        self.splitter_4.setObjectName(u"splitter_4")
        self.splitter_4.setOrientation(Qt.Horizontal)
        self.splitter_2 = QSplitter(self.splitter_4)
        self.splitter_2.setObjectName(u"splitter_2")
        self.splitter_2.setOrientation(Qt.Vertical)
        self.disasm = QTextEdit(self.splitter_2)
        self.disasm.setObjectName(u"disasm")
        self.splitter_2.addWidget(self.disasm)
        self.code = QTextEdit(self.splitter_2)
        self.code.setObjectName(u"code")
        self.splitter_2.addWidget(self.code)
        self.splitter_4.addWidget(self.splitter_2)
        self.splitter_3 = QSplitter(self.splitter_4)
        self.splitter_3.setObjectName(u"splitter_3")
        self.splitter_3.setOrientation(Qt.Vertical)
        self.regs = QTextEdit(self.splitter_3)
        self.regs.setObjectName(u"regs")
        self.splitter_3.addWidget(self.regs)
        self.backtrace = QTextEdit(self.splitter_3)
        self.backtrace.setObjectName(u"backtrace")
        self.splitter_3.addWidget(self.backtrace)
        self.splitter_4.addWidget(self.splitter_3)
        self.stack = QTextEdit(self.splitter_4)
        self.stack.setObjectName(u"stack")
        self.splitter_4.addWidget(self.stack)
        self.splitter_5.addWidget(self.splitter_4)
        self.splitter = QSplitter(self.splitter_5)
        self.splitter.setObjectName(u"splitter")
        self.splitter.setOrientation(Qt.Horizontal)
        self.main = QTextEdit(self.splitter)
        self.main.setObjectName(u"main")
        self.splitter.addWidget(self.main)
        self.ipython = QTextEdit(self.splitter)
        self.ipython.setObjectName(u"ipython")
        self.splitter.addWidget(self.ipython)
        self.splitter_5.addWidget(self.splitter)

        self.retranslateUi(PwnDbgGui)

        QMetaObject.connectSlotsByName(PwnDbgGui)
    # setupUi

    def retranslateUi(self, PwnDbgGui):
        PwnDbgGui.setWindowTitle(QCoreApplication.translate("PwnDbgGui", u"PwnDbgGui", None))
    # retranslateUi

