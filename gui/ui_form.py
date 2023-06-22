# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'form.ui'
##
## Created by: Qt User Interface Compiler version 6.5.0
##
## WARNING! All changes made in this file will be lost when recompiling UI file!
################################################################################

from PySide6.QtCore import (QCoreApplication, QMetaObject, QRect,
                            Qt)
from PySide6.QtWidgets import (QFrame, QPushButton, QSplitter, QTextBrowser, QTextEdit)


class Ui_PwnDbgGui(object):
    def setupUi(self, PwnDbgGui):
        if not PwnDbgGui.objectName():
            PwnDbgGui.setObjectName(u"PwnDbgGui")
        PwnDbgGui.resize(1380, 1066)
        self.line = QFrame(PwnDbgGui)
        self.line.setObjectName(u"line")
        self.line.setGeometry(QRect(10, 30, 1361, 16))
        self.line.setFrameShape(QFrame.Shape.HLine)
        self.line.setFrameShadow(QFrame.Shadow.Sunken)
        self.file_button = QPushButton(PwnDbgGui)
        self.file_button.setObjectName(u"file_button")
        self.file_button.setGeometry(QRect(10, 10, 80, 24))
        self.splitter_5 = QSplitter(PwnDbgGui)
        self.splitter_5.setObjectName(u"splitter_5")
        self.splitter_5.setGeometry(QRect(10, 40, 1361, 1021))
        self.splitter_5.setOrientation(Qt.Vertical)
        self.splitter_4 = QSplitter(self.splitter_5)
        self.splitter_4.setObjectName(u"splitter_4")
        self.splitter_4.setOrientation(Qt.Horizontal)
        self.splitter_2 = QSplitter(self.splitter_4)
        self.splitter_2.setObjectName(u"splitter_2")
        self.splitter_2.setOrientation(Qt.Vertical)
        self.disasm = QTextBrowser(self.splitter_2)
        self.disasm.setObjectName(u"disasm")
        self.splitter_2.addWidget(self.disasm)
        self.code = QTextBrowser(self.splitter_2)
        self.code.setObjectName(u"code")
        self.splitter_2.addWidget(self.code)
        self.splitter_4.addWidget(self.splitter_2)
        self.splitter_3 = QSplitter(self.splitter_4)
        self.splitter_3.setObjectName(u"splitter_3")
        self.splitter_3.setOrientation(Qt.Vertical)
        self.regs = QTextBrowser(self.splitter_3)
        self.regs.setObjectName(u"regs")
        self.splitter_3.addWidget(self.regs)
        self.io = QTextBrowser(self.splitter_3)
        self.io.setObjectName(u"io")
        self.splitter_3.addWidget(self.io)
        self.splitter_4.addWidget(self.splitter_3)
        self.stack = QTextBrowser(self.splitter_4)
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
        self.file_button.setText(QCoreApplication.translate("PwnDbgGui", u"Select File", None))
    # retranslateUi
