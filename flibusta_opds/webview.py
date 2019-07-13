import os
import sys

from PyQt5 import QtWidgets, QtCore, QtGui
from PyQt5.QtCore import QUrl, pyqtSlot
from PyQt5.QtNetwork import QNetworkProxy
from PyQt5.QtWebEngineWidgets import QWebEnginePage

from . import BASE_DIR, CURRENT_PROXY
from . import xml_parser
from .history import History
from .make_html import make_html_page
from .opds_requests import get_from_opds, RequestErr, get_main_opds, DownloadFile
from flibusta_opds.webviewwidget import Ui_Form
from . import PROXY_LIST, signals


class MyEvent(QtCore.QEvent):
    """Класс события

    Событие будет генерироваться при клике на ссылках. Будет использаватья вместо сигнал urlChanged
    """

    idType = QtCore.QEvent.registerEventType()

    def __init__(self, data):
        QtCore.QEvent.__init__(self, MyEvent.idType)
        self.data = data

    def get_data(self):
        return self.data


class WebEnginePage(QWebEnginePage):
    """Класс QWebEnginePage

    Перегружаем функцию acceptNavigationRequest чтобы перехватывать запрашиваемые урлы. При перехвате возбуждаем событие
    и обрабатываем урл.
    """

    def acceptNavigationRequest(self, url, _type, isMainFrame):
        """При запросе урла со схемой file возбуждает событие и запрещает загрузку этого урла"""
        if url.scheme() == 'file':
            QtCore.QCoreApplication.sendEvent(self.parent(), MyEvent(url.toLocalFile()))
            return False
        return True


class MainWidget(QtWidgets.QWidget):

    def __init__(self, parent=None):
        super().__init__(parent)
        self.history = History()
        self.baseUrl = QUrl.fromLocalFile(BASE_DIR)
        self.url = QUrl('http://flibusta.is')
        self.ui = Ui_Form()
        self.ui.setupUi(self)
        ################################################################################################################
        # Задаем прокси-сервер для приложения                                                                          #
        ################################################################################################################
        # todo: после установки соединения с прокси с помощью request установить этот прокси для всего приложения
        self.proxy = QNetworkProxy()
        # self.proxy.setHostName('37.182.199.214')  # 142.93.132.193
        # self.proxy.setPort(3128)  # 8080
        self.proxy.setType(QNetworkProxy.HttpProxy)
        # QNetworkProxy.setApplicationProxy(self.proxy)
        ################################################################################################################
        self.loadUI()

    # noinspection PyUnresolvedReferences
    def loadUI(self):
        self.setWindowIcon(QtGui.QIcon('./res/favicon.ico'))
        self.ui.progressBar.reset()
        self.ui.webView.setPage(WebEnginePage(self))
        self.ui.backBtn.setDisabled(True)
        self.ui.nextBtn.setDisabled(True)

        ################################################################################################################
        # ComboBox с прокси серверами                                                                                  #
        ################################################################################################################
        self.proxy_cbx = QtWidgets.QComboBox(self)
        self.proxy_cbx.setInsertPolicy(self.proxy_cbx.InsertAtTop)
        self.proxy_cbx.setEditable(True)
        self.proxy_cbx.setModel(QtCore.QStringListModel(PROXY_LIST))

        validator = QtGui.QRegExpValidator(QtCore.QRegExp(
            r'[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}:\d{1,5}'))

        self.proxy_cbx.setValidator(validator)
        ################################################################################################################
        self.proxy_label = QtWidgets.QLabel(f'Прокси {self.proxy.hostName()} : {self.proxy.port()}')
        self.setProxyBtn = QtWidgets.QPushButton('Установить прокси')

        hbox = QtWidgets.QHBoxLayout()
        hbox.addStretch()
        hbox.addWidget(self.proxy_label)
        hbox.addWidget(self.proxy_cbx)
        hbox.addWidget(self.setProxyBtn)
        self.ui.verticalLayout.insertLayout(0, hbox)

        #################################################################
        #   Обработка сигналов                                          #
        #################################################################
        self.ui.backBtn.clicked.connect(self.back_btn_clicked)
        self.ui.mainPageBtn.clicked.connect(self.main_page_btn_clicked)
        self.ui.nextBtn.clicked.connect(self.next_btn_clicked)
        self.setProxyBtn.clicked.connect(self.setPoxyBtn_clicked)
        signals.connect_to_proxy.connect(self.connect_to_proxy_signal)
        self.ui.searchBtn.clicked.connect(self.do_smtng)
        signals.progress.connect(self.ui.progressBar.setValue)
        self.ui.webView.titleChanged.connect(self.set_back_forward_btns_status)
        signals.file_name.connect(lambda x: self.ui.label.setText(x))
        signals.done.connect(self.ui.progressBar.reset)

        self.show()

    def do_smtng(self):
        url = 'http://testsite.alex.org/res/AUK-1M.pdf'
        get_main_opds(url)

    def setHtml(self, html):
        self.ui.webView.page().setHtml(html, self.baseUrl)
        self.ui.webView.page().runJavaScript('scrollTo(0,0);')

    @pyqtSlot()
    def connect_to_proxy_signal(self):
        """Обработка сигнала, поступившего при соединении с прокси-сервером"""
        self.set_proxy()

    @pyqtSlot()
    def set_proxy(self):
        """Установка прокси для приложения"""
        proxy, port = CURRENT_PROXY['https'].split(':')
        self.proxy.setHostName(proxy)
        self.proxy.setPort(int(port))
        # self.proxy.setType(QNetworkProxy.HttpProxy)
        self.proxy_label.setText(f'Прокси {proxy} : {port}')
        # print(self.proxy)
        QNetworkProxy.setApplicationProxy(self.proxy)

    @pyqtSlot()
    def setPoxyBtn_clicked(self):
        """Обработка нажатия кнопки установки прокси"""
        CURRENT_PROXY['https'] = self.proxy_cbx.currentText()
        self.set_proxy()

    @pyqtSlot()
    def set_back_forward_btns_status(self):
        """Установка активности кнопок вперед/назад в зависимости от истории посещений"""
        self.ui.backBtn.setEnabled(self.history.last.prev is not None)
        self.ui.nextBtn.setEnabled(self.history.last.next is not None)

    def customEvent(self, e):
        """Обработка события, возникающего при клике на ссылку"""
        if e.type() == MyEvent.idType:
            self.link_clicked(e.data)

    def get_html(self, url):
        QtWidgets.QApplication.setOverrideCursor(QtCore.Qt.WaitCursor)
        try:
            content = get_from_opds(url)
        finally:
            QtWidgets.QApplication.restoreOverrideCursor()
        # Если ссылка была на файл, то функция get_from_opds возвращает пустой объект.
        if not content:
            return None
        data = xml_parser.parser(fromstr=content)
        html = make_html_page(data)
        return html

    @pyqtSlot()
    def main_page_btn_clicked(self):
        try:
            html = self.get_html('/opds')
        except (RequestErr, xml_parser.XMLError) as e:
            print(e)
            self.msgbox(str(e))
            return
        self.setHtml(html)
        self.history.add('/opds')

    @pyqtSlot(QUrl)
    def link_clicked(self, url):
        """Переход по ссылке

        В историю добавляется посещенная ссылка.
        """
        try:
            html = self.get_html(url)
        except DownloadFile:
            return
        except (RequestErr, xml_parser.XMLError) as e:
            print(e)
            self.msgbox(str(e))
            return
        # если по ссылке находится файл, то метод get_html возвращает None
        # if not html:
        #     return
        self.setHtml(html)
        self.history.add(url)

    @pyqtSlot()
    def back_btn_clicked(self):
        """Навигация по истории назад"""
        link = self.history.previous()
        try:
            html = self.get_html(link.val)
        except (RequestErr, xml_parser.XMLError) as e:
            print(e)
            self.msgbox(str(e))
            return
        self.setHtml(html)

    @pyqtSlot()
    def next_btn_clicked(self):
        link = self.history.next()
        html = self.get_html(link.val)
        self.setHtml(html)

    def msgbox(self, msg):
        msgBox = QtWidgets.QMessageBox(QtWidgets.QMessageBox.Warning, 'Error', msg)
        msgBox.exec_()


def main():
    os.chdir(os.path.abspath(os.path.dirname(__file__)))
    sys.argv.append('--disable-web-security')
    print(QtCore.QT_VERSION_STR)
    app = QtWidgets.QApplication(sys.argv)
    win = MainWidget()
    status = app.exec()
    del win
    sys.exit(status)


if __name__ == '__main__':
    print(QtCore.QT_VERSION_STR)
    app = QtWidgets.QApplication(sys.argv)
    win = MainWidget()
    win.show()
    sys.exit(app.exec_())
