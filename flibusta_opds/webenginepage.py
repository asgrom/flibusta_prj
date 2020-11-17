import os

from applogger import applogger
from PyQt5.QtCore import QCoreApplication, QEvent, QUrl, pyqtSignal, pyqtSlot
from PyQt5.QtWebEngineWidgets import *
from PyQt5.QtWidgets import QFileDialog, QMessageBox

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
    fileName = pyqtSignal(str)
    downloadProgres = pyqtSignal(int, int)

    def __init__(self, *args, **kwargs):
        super(WebEnginePage, self).__init__(*args, **kwargs)
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
        download.finished.connect(lambda: self._fileDownloadFinished(download.state()))
        download.accept()
        self.fileName.emit(download.downloadFileName())
        download.downloadProgress.connect(self.downloadProgres.emit)

    @pyqtSlot()
    def _fileDownloadFinished(self, state):
        if state == QWebEngineDownloadItem.DownloadInterrupted:
            QMessageBox.critical(None, 'Download interrupted', f'{self.download.interruptReasonString()}')
        else:
            QMessageBox.information(None, '', 'Download completed')

    def acceptNavigationRequest(self, url: QUrl, _type, isMainFrame):
        """При запросе урла со схемой file возбуждает событие и запрещает загрузку этого урла"""
        if url.scheme() == 'file':
            QCoreApplication.sendEvent(self.parent(), MyEvent(url.path()))
            return False
        return super(WebEnginePage, self).acceptNavigationRequest(url, _type, isMainFrame)

    def getOpdsData(self) -> bytes:
        return bytes(self._opdsData)
