# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'webviewwidget.ui'
#
# Created by: PyQt5 UI code generator 5.12.2
#
# WARNING! All changes made in this file will be lost!

from PyQt5 import QtCore, QtGui, QtWidgets


class Ui_Form(object):
    def setupUi(self, Form):
        Form.setObjectName("Form")
        Form.resize(600, 500)
        Form.setMinimumSize(QtCore.QSize(600, 500))
        font = QtGui.QFont()
        font.setStyleStrategy(QtGui.QFont.PreferAntialias)
        Form.setFont(font)
        self.gridLayout_4 = QtWidgets.QGridLayout(Form)
        self.gridLayout_4.setObjectName("gridLayout_4")
        self.frame_download = QtWidgets.QFrame(Form)
        self.frame_download.setFrameShape(QtWidgets.QFrame.StyledPanel)
        self.frame_download.setFrameShadow(QtWidgets.QFrame.Raised)
        self.frame_download.setObjectName("frame_download")
        self.gridLayout_3 = QtWidgets.QGridLayout(self.frame_download)
        self.gridLayout_3.setContentsMargins(6, 6, 6, 6)
        self.gridLayout_3.setObjectName("gridLayout_3")
        self.gridLayout_2 = QtWidgets.QGridLayout()
        self.gridLayout_2.setObjectName("gridLayout_2")
        self.splitter_2 = QtWidgets.QSplitter(self.frame_download)
        self.splitter_2.setFrameShape(QtWidgets.QFrame.NoFrame)
        self.splitter_2.setOrientation(QtCore.Qt.Horizontal)
        self.splitter_2.setObjectName("splitter_2")
        self.backBtn = QtWidgets.QPushButton(self.splitter_2)
        self.backBtn.setObjectName("backBtn")
        self.nextBtn = QtWidgets.QPushButton(self.splitter_2)
        self.nextBtn.setObjectName("nextBtn")
        self.gridLayout_2.addWidget(self.splitter_2, 1, 0, 1, 1)
        self.mainPageBtn = QtWidgets.QPushButton(self.frame_download)
        self.mainPageBtn.setObjectName("mainPageBtn")
        self.gridLayout_2.addWidget(self.mainPageBtn, 0, 0, 1, 1)
        self.gridLayout_3.addLayout(self.gridLayout_2, 0, 0, 1, 1)
        self.gridLayout_4.addWidget(self.frame_download, 0, 0, 1, 1)
        self.frame_btn = QtWidgets.QFrame(Form)
        self.frame_btn.setFrameShape(QtWidgets.QFrame.StyledPanel)
        self.frame_btn.setFrameShadow(QtWidgets.QFrame.Raised)
        self.frame_btn.setObjectName("frame_btn")
        self.gridLayout = QtWidgets.QGridLayout(self.frame_btn)
        self.gridLayout.setContentsMargins(6, 6, 6, 6)
        self.gridLayout.setObjectName("gridLayout")
        self.verticalLayout = QtWidgets.QVBoxLayout()
        self.verticalLayout.setObjectName("verticalLayout")
        self.label = QtWidgets.QLabel(self.frame_btn)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.label.sizePolicy().hasHeightForWidth())
        self.label.setSizePolicy(sizePolicy)
        self.label.setObjectName("label")
        self.verticalLayout.addWidget(self.label)
        self.progressBar = QtWidgets.QProgressBar(self.frame_btn)
        self.progressBar.setProperty("value", 0)
        self.progressBar.setObjectName("progressBar")
        self.verticalLayout.addWidget(self.progressBar)
        self.gridLayout.addLayout(self.verticalLayout, 0, 0, 1, 1)
        self.gridLayout_4.addWidget(self.frame_btn, 1, 0, 1, 1)
        self.webView = QtWebEngineWidgets.QWebEngineView(Form)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.webView.sizePolicy().hasHeightForWidth())
        self.webView.setSizePolicy(sizePolicy)
        self.webView.setUrl(QtCore.QUrl("about:blank"))
        self.webView.setObjectName("webView")
        self.gridLayout_4.addWidget(self.webView, 2, 0, 1, 1)

        self.retranslateUi(Form)
        QtCore.QMetaObject.connectSlotsByName(Form)

    def retranslateUi(self, Form):
        _translate = QtCore.QCoreApplication.translate
        Form.setWindowTitle(_translate("Form", "Flibusta OPDS"))
        self.backBtn.setText(_translate("Form", "Назад"))
        self.nextBtn.setText(_translate("Form", "Вперед"))
        self.mainPageBtn.setText(_translate("Form", "Главная страница каталога"))
        self.label.setText(_translate("Form", "Загрузка файла"))


from PyQt5 import QtWebEngineWidgets
