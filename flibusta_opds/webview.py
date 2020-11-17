#!/usr/bin/env /home/alexandr/venv/qvenv/bin/python
# todo:
#   просмотреть возбуждение исключений raise
import os
import sys
import traceback

from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtNetwork import *
from PyQt5.QtWebEngineWidgets import *
from PyQt5.QtWidgets import *
from applogger import applogger
from requests import exceptions

from . import (BASE_DIR, CURRENT_PROXY, PROXY_LIST, opds_requests, signals,
               xml_parser)
from .get_proxy import get_proxy_list
from .history import History
from .make_html import make_html_page
from .opds_requests import RequestErr, get_from_opds
from .webviewwidget import Ui_Form

logger = applogger.get_logger(__name__, __file__)

URL = 'http://flibusta.is'


def uncaught_exception(ex_cls, val, tb):
    text = f'Uncaught exception:\n{ex_cls.__name__}: {val}:\n'
    text += ''.join(traceback.format_tb(tb))
    logger.error(text)
    QMessageBox.critical(None, '', 'Critical error')
    sys.exit()


sys.excepthook = uncaught_exception


class MyEvent(QEvent):
    """Класс события

    Событие будет генерироваться при клике на ссылках. Будет использаватья вместо сигнал urlChanged
    """

    idType = QEvent.registerEventType()

    def __init__(self, data):
        QEvent.__init__(self, MyEvent.idType)
        self.data = data

    def get_data(self):
        return self.data


class WebEnginePage(QWebEnginePage):
    """Класс QWebEnginePage

    Перегружаем функцию acceptNavigationRequest чтобы перехватывать запрашиваемые урлы. При перехвате возбуждаем событие
    и обрабатываем урл.
    """
    opdsDataDownloaded = pyqtSignal()
    fileName = pyqtSignal(str)
    downloadProgres = pyqtSignal(int, int)

    def __init__(self, *args, **kwargs):
        super(WebEnginePage, self).__init__(*args, **kwargs)
        self.qnam = QNetworkAccessManager()
        self.qnam.finished.connect(self._downloadFinished)
        self._opdsData = None
        self._reply = None  # type: QNetworkReply
        # сигнал генерируется при запросе на скачивание файла
        self.profile().downloadRequested.connect(self.on_downloadRequested)

    @pyqtSlot(QWebEngineDownloadItem)
    def on_downloadRequested(self, download: QWebEngineDownloadItem):
        # todo:
        #   переделать обработку сигналов
        #   Переделать диалог сохранения файла. НЕ УСТАНАВЛИВАЕТ КАТАЛОГ ЗАГРУЗКИ ПО-УМОЛЧАНИЮ!
        file, _ = QFileDialog.getSaveFileName(
            None, '',
            os.path.join(download.downloadDirectory(), download.downloadFileName()),
            'All (*)'
        )
        if not file:
            return
        download.setDownloadFileName(file)
        download.finished.connect(lambda: self.download_completed(download.state()))
        download.accept()
        self.fileName.emit(download.downloadFileName())
        download.downloadProgress.connect(self.downloadProgres.emit())

    @pyqtSlot()
    def download_completed(self, state):
        state = self.downloadItem.state()
        if state == QWebEngineDownloadItem.DownloadInterrupted:
            QMessageBox.critical(None, 'Download interrupted', f'{self.download.interruptReasonString()}')
        else:
            QMessageBox.information(None, '', 'Download completed')

    def acceptNavigationRequest(self, url: QUrl, _type, isMainFrame):
        """При запросе урла со схемой file возбуждает событие и запрещает загрузку этого урла"""
        if url.scheme() == 'file':
            request = QNetworkRequest(QUrl(URL + url.toLocalFile()))
            request.setAttribute(QNetworkRequest.RedirectPolicyAttribute, True)
            self.qnam.get(request)
            QCoreApplication.sendEvent(self.parent(), MyEvent(url.path()))
            return False
        return super(WebEnginePage, self).acceptNavigationRequest(url, _type, isMainFrame)

    def _downloadFinished(self, reply: QNetworkReply):
        if reply.error():
            logger.critical(f'Error download content\n{reply.errorString()}')
            return
        self._opdsData = reply.readAll()
        reply.deleteLater()
        self.opdsDataDownloaded.emit()

    def getOpdsData(self) -> bytes:
        return bytes(self._opdsData)


class MainWidget(QWidget):
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
        self.setWindowIcon(QIcon(os.path.join(os.path.dirname(__file__), './res/favicon.ico')))
        self.page = WebEnginePage(self)
        self.ui.webView.setPage(self.page)
        self.ui.backBtn.setDisabled(True)
        self.ui.nextBtn.setDisabled(True)
        self.ui.progressBar.setFormat('%v Kb')

        ################################################################################################################
        # ComboBox с прокси серверами                                                                                  #
        ################################################################################################################
        self.proxy_cbx = QComboBox(self)
        self.proxy_cbx.setInsertPolicy(self.proxy_cbx.InsertAtTop)
        self.proxy_cbx.setEditable(True)
        self.proxy_cbx.setSizeAdjustPolicy(QComboBox.AdjustToContents)
        self.proxy_cbx.setModel(QStringListModel(PROXY_LIST))
        validator = QRegExpValidator(QRegExp(
            r'[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}:\d{1,5}'))
        self.proxy_cbx.setValidator(validator)

        ################################################################################################################
        self.proxy_label = QLabel(f'Прокси {self.proxy.hostName()} : {self.proxy.port()}')
        self.setProxyBtn = QPushButton('Установить прокси')
        self.getProxyBtn = QPushButton('Получить список прокси')
        self.torBtn = QPushButton('Tor')

        hbox = QHBoxLayout()
        hbox.addWidget(self.torBtn)
        hbox.addWidget(self.getProxyBtn)
        hbox.addStretch()
        hbox.addWidget(self.proxy_label)
        hbox.addWidget(self.proxy_cbx)
        hbox.addWidget(self.setProxyBtn)
        self.ui.verticalLayout.insertLayout(0, hbox)
        self.ui.search_le.setAlignment(Qt.AlignLeft)

        #################################################################
        #   Обработка сигналов                                          #
        #################################################################
        self.ui.backBtn.clicked.connect(self.back_btn_clicked)
        self.ui.mainPageBtn.clicked.connect(self.main_page_btn_clicked)
        self.ui.nextBtn.clicked.connect(self.next_btn_clicked)
        self.setProxyBtn.clicked.connect(self.setPoxyBtn_clicked)
        # signals.connect_to_proxy получаем при удачном соединении с прокси
        signals.connect_to_proxy.connect(self.set_proxy)
        self.page.downloadProgres.connect(self.setDownloadProgress)
        self.ui.webView.titleChanged.connect(self.set_back_forward_btns_status)
        # signals.file_name получаем название скачиваемого файла
        self.page.fileName.connect(self.ui.label.setText)
        signals.change_proxy.connect(self.change_app_proxies)
        self.getProxyBtn.clicked.connect(self.get_proxy)
        self.ui.searchBtn.clicked.connect(self.search_on_opds)
        self.torBtn.clicked.connect(self.torBtn_clicked)
        # self.page.opdsDataDownloaded.connect(self.opdsXmlDownloaded)
        self.show()

    @pyqtSlot()
    def opdsXmlDownloaded(self):
        data = self.page.getOpdsData()
        print(data.decode())

    @pyqtSlot()
    def torBtn_clicked(self):
        CURRENT_PROXY.clear()
        CURRENT_PROXY.update(http=self.tor, https=self.tor)
        signals.connect_to_proxy.emit()

    @pyqtSlot(int, int)
    def setDownloadProgress(self, recieved, total):
        recieved = int(recieved / 1024)
        total = int(total / 1024)
        """Формат прогрессбара при скачивании файла со страницы сайта"""
        if self.ui.progressBar.maximum() != total:
            self.ui.progressBar.setMaximum(total)
        self.ui.progressBar.setValue(recieved)

    @pyqtSlot()
    def search_on_opds(self):
        QApplication.setOverrideCursor(Qt.WaitCursor)
        try:
            html = self.get_html('/opds/search', searchText=self.ui.search_le.text().strip())
        except Exception as e:
            self.msgbox(str(e))
            return
        finally:
            QApplication.restoreOverrideCursor()
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
        self.proxy_cbx.setModel(QStringListModel(PROXY_LIST))
        opds_requests.PROXIES.clear()

    @pyqtSlot()
    def get_proxy(self):
        """Палучаем новый список прокси и устанавливаем его"""
        QApplication.setOverrideCursor(Qt.WaitCursor)
        try:
            self.change_app_proxies(get_proxy_list())
        except Exception as e:
            self.msgbox(str(e))
        else:
            self.msgbox('Список прокси обновлен', title='Выполнено')
        finally:
            QApplication.restoreOverrideCursor()

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
        QApplication.setOverrideCursor(Qt.WaitCursor)
        try:
            content = get_from_opds(url, searchText)
        finally:
            QApplication.restoreOverrideCursor()
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
            msgBox = QMessageBox(QMessageBox.Warning, 'Error', msg)
        else:
            msgBox = QMessageBox(QMessageBox.Warning, title, msg)
        msgBox.exec_()


def main():
    print(f'Версия Qt {QT_VERSION_STR}')
    os.chdir(os.path.abspath(os.path.dirname(__file__)))
    sys.argv.append('--disable-web-security')
    app = QApplication(sys.argv)
    # установка таблицы стилей
    # file = QFile(os.path.join(os.path.dirname(__file__), 'css/stylesheet.qss'))
    # if file.open(QIODevice.ReadOnly | QIODevice.Text):
    #     qss = QTextStream(file).readAll()
    #     file.close()
    #     app.setStyleSheet(qss)

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
