__version__ = '0.2'

from os import path
import os
import json
from PyQt5.QtCore import pyqtSignal, QObject

BASE_DIR = path.dirname(__file__) + '/'

# текущий прокси. будет использоваться глобально для всего приложения
CURRENT_PROXY = dict()

if not path.exists(path.join(BASE_DIR, 'res')):
    os.mkdir(path.join(BASE_DIR, 'res'))
proxy_json_file = path.join(BASE_DIR, 'res/proxy.json')

try:
    with open(proxy_json_file) as f:
        PROXY_LIST = json.load(f)
except (FileNotFoundError, json.JSONDecoder):
    PROXY_LIST = list()


class Signals(QObject):
    progress = pyqtSignal(int)
    connect_to_proxy = pyqtSignal()
    file_name = pyqtSignal(str)
    done = pyqtSignal()


signals = Signals()
