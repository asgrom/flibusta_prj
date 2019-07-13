__version__ = '0.1'

from os import path
import json
from PyQt5.QtCore import pyqtSignal, QObject

BASE_DIR = path.dirname(__file__) + '/'

# текущий прокси. будет использоваться глобально для всего приложения
CURRENT_PROXY = dict()

proxy_json_file = path.join(BASE_DIR, 'res/proxy1.json')

with open(proxy_json_file) as f:
    PROXY_LIST = [':'.join(proxy) for proxy in json.load(f)]


class Signals(QObject):
    progress = pyqtSignal(int)
    connect_to_proxy = pyqtSignal()
    file_name = pyqtSignal(str)
    done = pyqtSignal()


signals = Signals()
