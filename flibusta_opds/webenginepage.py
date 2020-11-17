from PyQt5.QtWebEngineWidgets import *
from PyQt5.QtCore import pyqtSlot, pyqtSignal, QCoreApplication, QEvent
from PyQt5.QtCore import QUrl
from PyQt5.QtNetwork import QNetworkReply, QNetworkAccessManager, QNetworkRequest
from applogger import applogger

logger = applogger.get_logger(__name__, __file__)


URL = 'http://flibusta.is'


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
        # сигнал генерируется при запросе на скачивание файла
        self.profile().downloadRequested.connect(self.on_downloadRequested)

    @pyqtSlot(QWebEngineDownloadItem)
    def on_downloadRequested(self, download: QWebEngineDownloadItem):
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
        download.downloadProgress.connect(self.downloadProgres.emit)

    @pyqtSlot()
    def download_completed(self, state):
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
