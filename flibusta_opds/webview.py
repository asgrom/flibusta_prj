# todo:
#   просмотреть возбуждение исключений raise
import os
import sys
import traceback

from applogger import applogger
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtNetwork import *
from PyQt5.QtWebEngineWidgets import *
from PyQt5.QtWidgets import *
from requests import exceptions

from . import BASE_DIR, CURRENT_PROXY, PROXY_LIST, signals, xml_parser
from .get_proxy import get_proxy_list
from .history import History
from .make_html import make_html_page
from .webenginepage import MyEvent, WebEnginePage
from .mainwidget_ui import Ui_Form

logger = applogger.get_logger(__name__, __file__)


def uncaught_exception(ex_cls, val, tb):
    text = f'Uncaught exception:\n{ex_cls.__name__}: {val}:\n'
    text += ''.join(traceback.format_tb(tb))
    logger.error(text)
    QMessageBox.critical(None, '', 'Critical error')
    qApp.quit()


sys.excepthook = uncaught_exception


class MainWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.history = History()
        self.baseUrl = QUrl.fromLocalFile(BASE_DIR)
        self.qnam = QNetworkAccessManager()
        self._htmlData: bytes = None  # контент страницы
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
        self.setWindowIcon(QIcon(QPixmap(os.path.join(os.path.dirname(__file__), 'images/flibusta.png'))))
        self.webPage = WebEnginePage(self)
        self.ui.webView.setPage(self.webPage)
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
        self.webPage.downloadProgres.connect(self.setDownloadProgress)
        self.ui.webView.titleChanged.connect(self.set_back_forward_btns_status)
        # signals.file_name получаем название скачиваемого файла
        self.webPage.fileName.connect(self.ui.label.setText)
        signals.change_proxy.connect(self.change_app_proxies)
        self.getProxyBtn.clicked.connect(self.get_proxy)
        self.ui.searchBtn.clicked.connect(self.search_on_opds)
        self.torBtn.clicked.connect(self.torBtn_clicked)
        self.qnam.finished.connect(self.qnamFinished)
        self.show()

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

    def qnamFinished(self, reply: QNetworkReply):
        # todo:
        #   при возникновении ошибки загрузки, удалять прокси из списка.
        try:
            if reply.error():
                logger.error(f'Ошибка загрузки данных с сайта\n{reply.errorString()}')
                QMessageBox.critical(self, 'Error', f'Ошибка загрузки данных с сайта\n{reply.errorString()}')
                self._htmlData = None
                return
            self._htmlData = bytes(reply.readAll())
            reply.deleteLater()
        finally:
            reply.deleteLater()
            if self._loop.isRunning():
                self._loop.quit()

    @pyqtSlot()
    def search_on_opds(self):
        try:
            html = self.get_html('/opds/search', searchText=self.ui.search_le.text().strip())
        except Exception as e:
            logger.exception('')
            self.msgbox(str(e))
            return
        self.setHtml(html)
        self.history.add('/opds/search')

    @pyqtSlot()
    def change_app_proxies(self):
        """Установка списка прокси в выпадающий список"""
        PROXY_LIST.remove(CURRENT_PROXY['http'])
        CURRENT_PROXY.clear()
        self.proxy_label.setText('Прокси: ')
        self.proxy_cbx.setModel(QStringListModel(PROXY_LIST))

    @pyqtSlot()
    def get_proxy(self):
        """Палучаем новый список прокси и устанавливаем его"""
        QApplication.setOverrideCursor(Qt.WaitCursor)
        try:
            PROXY_LIST.clear()
            PROXY_LIST.extend(get_proxy_list())
            self.proxy_cbx.setModel(QStringListModel(PROXY_LIST))
        except Exception as e:
            logger.exception('')
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
        self.set_proxy()

    @pyqtSlot()
    def set_back_forward_btns_status(self):
        """Установка активности кнопок вперед/назад в зависимости от истории посещений"""
        self.ui.backBtn.setEnabled((self.history.last.prev is not None) or (self.webPage.history().canGoBack()))
        self.ui.nextBtn.setEnabled(self.history.last.next is not None)

    def customEvent(self, e):
        """Обработка события, возникающего при клике на ссылку"""
        if e.type() == MyEvent.idType:
            self.link_clicked(e.data)

    def get_html(self, url, searchText=None):
        QApplication.setOverrideCursor(Qt.WaitCursor)
        query = QUrlQuery()
        query.setQueryItems([('searchType', 'authors'), ('searchTerm', f'{{{searchText}}}')])
        url_ = QUrl('http://flibusta.is')
        url_.setPath(url)
        if url == '/opds/search':
            url_.setQuery(query)
        request = QNetworkRequest(url_)
        request.setAttribute(QNetworkRequest.FollowRedirectsAttribute, True)
        self._loop = QEventLoop()
        self.qnam.get(request)
        self._loop.exec_()
        QApplication.restoreOverrideCursor()
        if not self._htmlData:
            return

        # с использованием requests
        # QApplication.setOverrideCursor(Qt.WaitCursor)
        # try:
        #     content = get_from_opds(url, searchText)
        # finally:
        #     QApplication.restoreOverrideCursor()

        data = xml_parser.parser(fromstr=self._htmlData)
        html = make_html_page(data)
        return html

    @pyqtSlot()
    def main_page_btn_clicked(self):
        try:
            html = self.get_html('/opds')
        except (xml_parser.XMLError, exceptions.HTTPError) as e:
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
        except (xml_parser.XMLError, exceptions.HTTPError) as e:
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
        if self.webPage.history().canGoBack():
            self.webPage.history().back()
            return

        link = self.history.previous()
        try:
            html = self.get_html(link.val)
        except (xml_parser.XMLError) as e:
            logger.exception('')
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
