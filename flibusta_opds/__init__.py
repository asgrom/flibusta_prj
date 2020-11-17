__version__ = '0.2'

import json
import os
from os import path

from PyQt5.QtCore import pyqtSignal, QObject

BASE_DIR = path.dirname(__file__) + '/'

# текущий прокси. будет использоваться глобально для всего приложения
CURRENT_PROXY = dict()

# список прокси серверов
PROXY_LIST = list()

if not path.exists(path.join(BASE_DIR, 'res')):
    os.mkdir(path.join(BASE_DIR, 'res'))

proxy_json_file = path.join(BASE_DIR, 'res/proxy.json')

try:
    with open(proxy_json_file) as f:
        PROXY_LIST.extend(json.load(f))
except Exception:
    pass


class Signals(QObject):
    # соединение с прокси
    connect_to_proxy = pyqtSignal()
    change_proxy = pyqtSignal()


signals = Signals()
