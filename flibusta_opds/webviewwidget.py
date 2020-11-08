# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file '/home/alexandr/PycharmProjects/flibusta_prj/flibusta_opds/ui/webviewwidget_v2.ui'
#
# Created by: PyQt5 UI code generator 5.13.1
#
# WARNING! All changes made in this file will be lost!


from PyQt5 import QtCore, QtGui, QtWidgets


class Ui_Form(object):
    def setupUi(self, Form):
        Form.setObjectName("Form")
        Form.resize(956, 690)
        Form.setMinimumSize(QtCore.QSize(600, 500))
        font = QtGui.QFont()
        font.setStyleStrategy(QtGui.QFont.PreferAntialias)
        Form.setFont(font)
        self.gridLayout_2 = QtWidgets.QGridLayout(Form)
        self.gridLayout_2.setObjectName("gridLayout_2")
        self.frame_download = QtWidgets.QFrame(Form)
        self.frame_download.setFrameShape(QtWidgets.QFrame.StyledPanel)
        self.frame_download.setFrameShadow(QtWidgets.QFrame.Raised)
        self.frame_download.setObjectName("frame_download")
        self.horizontalLayout_3 = QtWidgets.QHBoxLayout(self.frame_download)
        self.horizontalLayout_3.setObjectName("horizontalLayout_3")
        self.horizontalLayout_2 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_2.setObjectName("horizontalLayout_2")
        self.mainPageBtn = QtWidgets.QPushButton(self.frame_download)
        self.mainPageBtn.setObjectName("mainPageBtn")
        self.horizontalLayout_2.addWidget(self.mainPageBtn)
        self.backBtn = QtWidgets.QPushButton(self.frame_download)
        self.backBtn.setObjectName("backBtn")
        self.horizontalLayout_2.addWidget(self.backBtn)
        self.nextBtn = QtWidgets.QPushButton(self.frame_download)
        self.nextBtn.setObjectName("nextBtn")
        self.horizontalLayout_2.addWidget(self.nextBtn)
        self.horizontalLayout_3.addLayout(self.horizontalLayout_2)
        self.horizontalLayout = QtWidgets.QHBoxLayout()
        self.horizontalLayout.setObjectName("horizontalLayout")
        self.search_le = QtWidgets.QLineEdit(self.frame_download)
        self.search_le.setToolTip("")
        self.search_le.setToolTipDuration(-1)
        self.search_le.setWhatsThis("")
        self.search_le.setLayoutDirection(QtCore.Qt.LeftToRight)
        self.search_le.setObjectName("search_le")
        self.horizontalLayout.addWidget(self.search_le)
        self.searchBtn = QtWidgets.QPushButton(self.frame_download)
        self.searchBtn.setObjectName("searchBtn")
        self.horizontalLayout.addWidget(self.searchBtn)
        self.horizontalLayout_3.addLayout(self.horizontalLayout)
        self.gridLayout_2.addWidget(self.frame_download, 0, 0, 1, 1)
        self.frame_btn = QtWidgets.QFrame(Form)
        self.frame_btn.setFrameShape(QtWidgets.QFrame.StyledPanel)
        self.frame_btn.setFrameShadow(QtWidgets.QFrame.Raised)
        self.frame_btn.setObjectName("frame_btn")
        self.verticalLayout = QtWidgets.QVBoxLayout(self.frame_btn)
        self.verticalLayout.setObjectName("verticalLayout")
        self.horizontalLayout_4 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_4.setObjectName("horizontalLayout_4")
        self.label = QtWidgets.QLabel(self.frame_btn)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.label.sizePolicy().hasHeightForWidth())
        self.label.setSizePolicy(sizePolicy)
        self.label.setObjectName("label")
        self.horizontalLayout_4.addWidget(self.label)
        self.progressBar = QtWidgets.QProgressBar(self.frame_btn)
        self.progressBar.setProperty("value", 0)
        self.progressBar.setObjectName("progressBar")
        self.horizontalLayout_4.addWidget(self.progressBar)
        self.verticalLayout.addLayout(self.horizontalLayout_4)
        self.gridLayout_2.addWidget(self.frame_btn, 1, 0, 1, 1)
        self.webView = QtWebEngineWidgets.QWebEngineView(Form)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.webView.sizePolicy().hasHeightForWidth())
        self.webView.setSizePolicy(sizePolicy)
        self.webView.setProperty("url", QtCore.QUrl("about:blank"))
        self.webView.setObjectName("webView")
        self.gridLayout_2.addWidget(self.webView, 2, 0, 1, 1)

        self.retranslateUi(Form)
        QtCore.QMetaObject.connectSlotsByName(Form)

    def retranslateUi(self, Form):
        _translate = QtCore.QCoreApplication.translate
        Form.setWindowTitle(_translate("Form", "Flibusta OPDS"))
        self.mainPageBtn.setText(_translate("Form", "Главная страница каталога"))
        self.backBtn.setText(_translate("Form", "Назад"))
        self.nextBtn.setText(_translate("Form", "Вперед"))
        self.searchBtn.setText(_translate("Form", "Найти"))
        self.label.setText(_translate("Form", "Загрузка файла"))
from PyQt5 import QtWebEngineWidgets
