__version__ = '0.1'

from os import path
import json
from PyQt5.QtCore import pyqtSignal, QObject

BASE_DIR = path.dirname(__file__) + '/'

# текущий прокси. будет использоваться глобально для всего приложения
CURRENT_PROXY = dict()

proxy_json_file = path.join(BASE_DIR, 'res/proxy.json')

with open(proxy_json_file) as f:
    try:
        PROXY_LIST = json.load(f)
    except json.JSONDecodeError:
        PROXY_LIST = list()


class Signals(QObject):
    progress = pyqtSignal(int)
    connect_to_proxy = pyqtSignal()
    file_name = pyqtSignal(str)
    done = pyqtSignal()


signals = Signals()
