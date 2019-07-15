import os
import re
from threading import Thread

from PyQt5.QtCore import QDir
from PyQt5.QtWidgets import QFileDialog
from requests import request, exceptions
from user_agent import generate_user_agent

from . import PROXY_LIST, signals, CURRENT_PROXY


class RequestErr(Exception):
    pass


class DownloadFile(Exception):
    pass


def get_dirname_to_save():
    """Вызывает диалог выбора каталога для сохраниния загрузки

    По-умолчанию начальный каталог устанавливается как папка downloads в корневом каталоге пакета"""
    dir_name = QFileDialog.getExistingDirectory(
        parent=None, caption='Каталог для загрузки',
        directory=os.path.join(QDir.currentPath(), 'downloads'),
        options=QFileDialog.ShowDirsOnly)
    return dir_name


PROXIES = []

user_agent = generate_user_agent('linux', 'chrome')

URL = 'https://flibusta.is'

# PROXIES = [
#     {
#         'http': '46.218.155.194:3128',
#         'https': '46.218.155.194:3128'
#     },
#     {
#         'http': '142.93.132.193:8080',
#         'https': '142.93.132.193:8080'
#     },
#     {
#         'http': '217.69.14.55:3128',
#         'https': '217.69.14.55:3128'
#     },
#     {
#         'http': '37.182.199.214:3128',
#         'https': '37.182.199.214:3128'
#     },
#     {
#         'http': '84.22.139.241:3128',
#         'https': '84.22.139.241:3128'
#     },
#     {
#         'http': '51.77.210.229:3128',
#         'https': '51.77.210.229:3128'
#     },
#     {
#         'https': '185.162.235.32:8082'
#     }
# ]

# список типов поиска
SEARCH_TYPE = ['authors', 'books']

# данные, которые будем отправлять для поиска
# соблюдать очередность аргументов!!!
# сначала тип поиска(книга, автор), потом строка поиска
search_params = {
    'searchType': '',
    'searchTerm': '',
    'pageNumber': None
}


def generate_proxies():
    proxies = [{'https': proxy} for proxy in PROXY_LIST]
    PROXIES.clear()
    PROXIES.extend(proxies)


def is_file(headers):
    """Прверка является ли ссылка ссылкой на файл
    """
    content_type = headers['content-type']
    if 'text/html' not in content_type and 'xml' not in content_type:
        return True
    return False


def get_file_name(response):
    """Получаем и возвращаем имя файла по ссылке.

    Имя файла берется из заголовка ответа от сервера. Если в заголовке его нет, то имя берется из самой ссылки.
    """

    try:
        filename = re.search(r'filename=\"?([^\"?]+)', response.headers['content-disposition'])
        return filename.group(1)
    except KeyError:
        return os.path.basename(response.url)


def download_file(res, file_dest, size):
    """ Скачивание файла

    Файл скачиваем кусками размером, заданным в переменной size. При скачивании файла изменяем прогресс-бар.
    """
    chunk = True
    i = 0
    fsize = int(res.headers['content-length'])
    delta = size * 100 / fsize
    signals.file_name.emit(os.path.basename(file_dest))
    with open(file_dest, 'wb') as f:
        try:
            while chunk:
                chunk = res.raw.read(size)
                if chunk:
                    f.write(chunk)
                    i += delta
                    signals.progress.emit(i)
        except Exception as e:
            raise RequestErr(f'ОШИБКА СКАЧИВАНИЯ ФАЙЛА\n{e}')
        finally:
            signals.done.emit()


def get_main_opds(url):
    """Получаем главную страницу каталога"""
    d = get_dirname_to_save()
    r = request('get', url, stream=True)
    fname = get_file_name(r)
    file_dest = os.path.join(d, fname)
    download_file(r, file_dest, 1024 * 128)


def get_from_opds(url, txt=None):
    """Сделать запрос по ссылке

    Производится проверка - является ли ссылка файлом или страницей. Если по ссылке находится файл, то происходит
    загрузка файла.
    """
    res = None
    size = 1024 * 128

    if not PROXIES:
        generate_proxies()

    if not txt:
        params = None
    else:
        params = dict(searchTerm=txt)

    if CURRENT_PROXY:
        try:
            res = request('get', URL + url, proxies=CURRENT_PROXY, headers={'user-agent': user_agent}, params=params,
                          stream=True, timeout=(10, 30))
        except (exceptions.ConnectionError, exceptions.ConnectTimeout) as e:
            print(f'{CURRENT_PROXY}\n{e}')
            CURRENT_PROXY.clear()
    else:
        for proxy in PROXIES:
            try:
                res = request('get', URL + url, proxies=proxy, headers={'user-agent': user_agent}, params=params,
                              stream=True, timeout=(10, 30))
                CURRENT_PROXY.update(proxy)
                break
            except (exceptions.ConnectTimeout, exceptions.ConnectionError) as e:
                print(f'{proxy}\n{e}')
    if not res:
        raise RequestErr('ОШИБКА СОЕДИНЕНИЯ')

    res.raise_for_status()

    signals.connect_to_proxy.emit()

    if not is_file(res.headers):
        return res.content

    dir_name = get_dirname_to_save()
    fname = get_file_name(res)
    file_dest = os.path.join(dir_name, fname)

    thread = Thread(target=download_file,
                    kwargs=dict(res=res, size=size, file_dest=file_dest))
    thread.start()
    raise DownloadFile('Скачивание файла')
