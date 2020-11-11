# todo:
#   просмотреть возбуждение исключений raise
import os
import sys
import traceback

from applogger import applogger
from PyQt5 import QtCore, QtGui, QtWebEngineWidgets, QtWidgets
from PyQt5.QtCore import *
from PyQt5.QtNetwork import QNetworkProxy
from PyQt5.QtWebEngineWidgets import QWebEnginePage
from PyQt5.QtWidgets import *
from requests import exceptions

from . import (BASE_DIR, CURRENT_PROXY, PROXY_LIST, opds_requests, signals,
               xml_parser)
from .get_proxy import get_proxy_list
from .history import History
from .make_html import make_html_page
from .opds_requests import RequestErr, get_from_opds
from .webviewwidget import Ui_Form

logger = applogger.get_logger(__name__, __file__)


def uncaught_exception(ex_cls, val, tb):
    text = f'Uncaught exception:\n{ex_cls.__name__}: {val}:\n'
    text += ''.join(traceback.format_tb(tb))
    logger.error(text)
    QMessageBox.critical(None, '', 'Critical error')
    sys.exit()


sys.excepthook = uncaught_exception


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

    def __init__(self, *args, **kwargs):
        super(WebEnginePage, self).__init__(*args, **kwargs)
        # сигнал генерируется при запросе на скачивание файла
        self.profile().downloadRequested.connect(self.on_downloadRequested)

    @QtCore.pyqtSlot(QtWebEngineWidgets.QWebEngineDownloadItem)
    def on_downloadRequested(self, download: QtWebEngineWidgets.QWebEngineDownloadItem):
        self.downloadItem = download
        self.file, _ = QFileDialog.getSaveFileName(None, '', self.downloadItem.path(), 'All (*)')
        if not self.file:
            return
        self.downloadItem.setPath(self.file)
        self.downloadItem.finished.connect(self.download_completed)
        self.downloadItem.accept()
        self.downloadItem.downloadProgress.connect(self.download_progress)
        self.downloadItem.downloadProgress.connect(lambda rec, tot: signals.progress.emit(int(rec / 1024), int(tot / 1024)))

    @pyqtSlot('qint64', 'qint64')
    def download_progress(self, received, total):
        signals.file_name.emit('{0}\t{1} Kb'.format(
            os.path.basename(self.file), str(int(received / 1024))))

    @pyqtSlot()
    def download_completed(self):
        state = self.downloadItem.state()
        if state == QtWebEngineWidgets.QWebEngineDownloadItem.DownloadInterrupted:
            QMessageBox.critical(self.parent(), 'Download interrupted', f'{self.download.interruptReasonString()}')
        else:
            QMessageBox.information(self.parent(), '', 'Download completed')

    def acceptNavigationRequest(self, url: QUrl, _type, isMainFrame):
        """При запросе урла со схемой file возбуждает событие и запрещает загрузку этого урла"""
        if url.scheme() == 'file':
            QtCore.QCoreApplication.sendEvent(self.parent(), MyEvent(url.path()))
            return False
        return super(WebEnginePage, self).acceptNavigationRequest(url, _type, isMainFrame)


class MainWidget(QtWidgets.QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.history = History()
        self.baseUrl = QUrl.fromLocalFile(BASE_DIR)
        self.ui = Ui_Form()
        self.ui.setupUi(self)
        self.tor = '127.0.0.1:8118'
        ################################################################################################################
        # Задаем прокси-сервер для приложения                                                                          #
        ################################################################################################################
        self.proxy = QNetworkProxy()
        self.proxy.setType(QNetworkProxy.HttpProxy)
        ################################################################################################################
        self.loadUI()

    # noinspection PyUnresolvedReferences
    def loadUI(self):
        self.setWindowIcon(QtGui.QIcon('./res/favicon.ico'))
        self.page = WebEnginePage(self)
        self.ui.webView.setPage(self.page)
        self.ui.backBtn.setDisabled(True)
        self.ui.nextBtn.setDisabled(True)
        self.ui.progressBar.setFormat('%v Kb')

        ################################################################################################################
        # ComboBox с прокси серверами                                                                                  #
        ################################################################################################################
        self.proxy_cbx = QtWidgets.QComboBox(self)
        self.proxy_cbx.setInsertPolicy(self.proxy_cbx.InsertAtTop)
        self.proxy_cbx.setEditable(True)
        self.proxy_cbx.setSizeAdjustPolicy(QtWidgets.QComboBox.AdjustToContents)
        self.proxy_cbx.setModel(QtCore.QStringListModel(PROXY_LIST))
        validator = QtGui.QRegExpValidator(QtCore.QRegExp(
            r'[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}:\d{1,5}'))
        self.proxy_cbx.setValidator(validator)

        ################################################################################################################
        self.proxy_label = QtWidgets.QLabel(f'Прокси {self.proxy.hostName()} : {self.proxy.port()}')
        self.setProxyBtn = QtWidgets.QPushButton('Установить прокси')
        self.getProxyBtn = QtWidgets.QPushButton('Получить список прокси')
        self.torBtn = QtWidgets.QPushButton('Tor')

        hbox = QtWidgets.QHBoxLayout()
        hbox.addWidget(self.torBtn)
        hbox.addWidget(self.getProxyBtn)
        hbox.addStretch()
        hbox.addWidget(self.proxy_label)
        hbox.addWidget(self.proxy_cbx)
        hbox.addWidget(self.setProxyBtn)
        self.ui.verticalLayout.insertLayout(0, hbox)
        self.ui.search_le.setAlignment(QtCore.Qt.AlignLeft)

        #################################################################
        #   Обработка сигналов                                          #
        #################################################################
        self.ui.backBtn.clicked.connect(self.back_btn_clicked)
        self.ui.mainPageBtn.clicked.connect(self.main_page_btn_clicked)
        self.ui.nextBtn.clicked.connect(self.next_btn_clicked)
        self.setProxyBtn.clicked.connect(self.setPoxyBtn_clicked)
        # signals.connect_to_proxy получаем при удачном соединении с прокси
        signals.connect_to_proxy.connect(self.set_proxy)
        signals.progress.connect(self.mod_progressbar)
        self.ui.webView.titleChanged.connect(self.set_back_forward_btns_status)
        # signals.file_name получаем название скачиваемого файла
        signals.file_name.connect(self.ui.label.setText)
        signals.change_proxy.connect(self.change_app_proxies)
        self.getProxyBtn.clicked.connect(self.get_proxy)
        self.ui.searchBtn.clicked.connect(self.search_on_opds)
        self.torBtn.clicked.connect(self.torBtn_clicked)
        self.show()

    @pyqtSlot()
    def torBtn_clicked(self):
        CURRENT_PROXY.clear()
        CURRENT_PROXY.update(http=self.tor, https=self.tor)
        signals.connect_to_proxy.emit()

    @pyqtSlot('qint64', 'qint64')
    def mod_progressbar(self, recieved, total):
        """Формат прогрессбара при скачивании файла со страницы сайта"""
        if self.ui.progressBar.maximum() != total:
            self.ui.progressBar.setMaximum(total)
        self.ui.progressBar.setValue(recieved)

    @pyqtSlot()
    def search_on_opds(self):
        QtWidgets.QApplication.setOverrideCursor(QtCore.Qt.WaitCursor)
        try:
            html = self.get_html('/opds/search', searchText=self.ui.search_le.text().strip())
        except Exception as e:
            self.msgbox(str(e))
            return
        finally:
            QtWidgets.QApplication.restoreOverrideCursor()
        self.setHtml(html)
        self.history.add('/opds/search')

    @pyqtSlot()
    def change_app_proxies(self, proxy_list=None):
        """Установка списка прокси в выпадающий список"""
        if not proxy_list:
            try:
                PROXY_LIST.remove(CURRENT_PROXY['http'])
            except Exception:
                pass
        else:
            PROXY_LIST.clear()
            PROXY_LIST.extend(proxy_list)
        CURRENT_PROXY.clear()
        self.proxy_label.setText('Прокси: ')
        self.proxy_cbx.setModel(QtCore.QStringListModel(PROXY_LIST))
        opds_requests.PROXIES.clear()

    @pyqtSlot()
    def get_proxy(self):
        """Палучаем новый список прокси и устанавливаем его"""
        QtWidgets.QApplication.setOverrideCursor(QtCore.Qt.WaitCursor)
        try:
            self.change_app_proxies(get_proxy_list())
        except Exception as e:
            self.msgbox(str(e))
        else:
            self.msgbox('Список прокси обновлен', title='Выполнено')
        finally:
            QtWidgets.QApplication.restoreOverrideCursor()

    def setHtml(self, html):
        self.ui.webView.page().setHtml(html, self.baseUrl)
        self.ui.webView.page().runJavaScript('scrollTo(0,0);')

    @pyqtSlot()
    def set_proxy(self):
        """Установка прокси для приложения"""
        proxy, port = CURRENT_PROXY['http'].split(':')
        self.proxy.setHostName(proxy)
        self.proxy.setPort(int(port))
        self.proxy_label.setText(f'Прокси {proxy} : {port}')
        QNetworkProxy.setApplicationProxy(self.proxy)

    @pyqtSlot()
    def setPoxyBtn_clicked(self):
        """Обработка нажатия кнопки установки прокси"""
        CURRENT_PROXY['http'] = self.proxy_cbx.currentText()
        PROXY_LIST.append(self.proxy_cbx.currentText())
        opds_requests.PROXIES.clear()
        self.set_proxy()

    @pyqtSlot()
    def set_back_forward_btns_status(self):
        """Установка активности кнопок вперед/назад в зависимости от истории посещений"""
        self.ui.backBtn.setEnabled((self.history.last.prev is not None) or (self.page.history().canGoBack()))
        self.ui.nextBtn.setEnabled(self.history.last.next is not None)

    def customEvent(self, e):
        """Обработка события, возникающего при клике на ссылку"""
        if e.type() == MyEvent.idType:
            self.link_clicked(e.data)

    def get_html(self, url, searchText=None):
        QtWidgets.QApplication.setOverrideCursor(QtCore.Qt.WaitCursor)
        try:
            content = get_from_opds(url, searchText)
        finally:
            QtWidgets.QApplication.restoreOverrideCursor()
        data = xml_parser.parser(fromstr=content)
        html = make_html_page(data)
        return html

    @pyqtSlot()
    def main_page_btn_clicked(self):
        try:
            html = self.get_html('/opds')
        except (RequestErr, xml_parser.XMLError, exceptions.HTTPError) as e:
            logger.exception('')
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
        except (RequestErr, xml_parser.XMLError, exceptions.HTTPError) as e:
            logger.exception('')
            self.msgbox(str(e))
            return
        self.setHtml(html)
        self.history.add(url)

    @pyqtSlot()
    def back_btn_clicked(self):
        """Навигация по истории назад"""

        # если история в QWebEnginePage на текущей странице не пуста, то используем эту историю для навигации.
        # иначе загружаем данные с opds
        if self.page.history().canGoBack():
            self.page.history().back()
            return

        link = self.history.previous()
        try:
            html = self.get_html(link.val)
        except (RequestErr, xml_parser.XMLError) as e:
            # print(e)
            self.msgbox(str(e))
            return
        self.setHtml(html)

    @pyqtSlot()
    def next_btn_clicked(self):
        link = self.history.next()
        html = self.get_html(link.val)
        self.setHtml(html)

    @staticmethod
    def msgbox(msg, title=None):
        if not title:
            msgBox = QtWidgets.QMessageBox(QtWidgets.QMessageBox.Warning, 'Error', msg)
        else:
            msgBox = QtWidgets.QMessageBox(QtWidgets.QMessageBox.Warning, title, msg)
        msgBox.exec_()


def main():
    os.chdir(os.path.abspath(os.path.dirname(__file__)))
    sys.argv.append('--disable-web-security')
    app = QtWidgets.QApplication(sys.argv)
    # with open('css/stylesheet.qss') as f:
    # app.setStyleSheet(f.read())
    from qtl18n_ru import localization
    localization.setupRussianLang(app)
    win = MainWidget()
    status = app.exec_()

    import json

    from . import proxy_json_file
    with open(proxy_json_file, 'w') as f:
        json.dump(PROXY_LIST, f, ensure_ascii=False, indent=2)

    sys.exit(status)


if __name__ == '__main__':
    main()
