from applogger import applogger
from requests import request, exceptions
from user_agent import generate_user_agent

from . import PROXY_LIST, signals, CURRENT_PROXY


class RequestErr(Exception):
    pass


# class DownloadFile(Exception):
#     pass


logger = applogger.get_logger(__name__, __file__)

PROXIES = []

# URL = 'https://flibusta.appspot.com/'
URL = 'http://flibusta.is/'


# список типов поиска
# SEARCH_TYPE = ['authors', 'books']

# данные, которые будем отправлять для поиска
# соблюдать очередность аргументов!!!
# сначала тип поиска(книга, автор), потом строка поиска
# search_params = {
#     'searchType': '',
#     'searchTerm': '',
#     'pageNumber': None
# }


def generate_proxies():
    PROXIES.clear()
    PROXIES.extend([{'http': proxy, 'https': proxy} for proxy in PROXY_LIST])


def is_file(headers):
    """Прверка является ли ссылка ссылкой на файл
    """
    content_type = headers['content-type']
    if 'text/html' not in content_type and 'xml' not in content_type:
        return True
    return False


# def get_file_name(response):
#     """Получаем и возвращаем имя файла по ссылке.
#
#     Имя файла берется из заголовка ответа от сервера. Если в заголовке его нет, то имя берется из самой ссылки.
#     """
#     try:
#         filename = re.search(r'filename=\"?([^\"?]+)', response.headers['content-disposition'])
#         file, _ = QFileDialog.getSaveFileName(
#             None, '',
#             os.path.join(
#                 QStandardPaths.writableLocation(QStandardPaths.DownloadLocation),
#                 filename.group(1)),
#             '*')
#         return file
#     except KeyError:
#         logger.exception('')
#         return os.path.basename(response.url)
#

# def download_file(res, file_dest):
#     """ Скачивание файла
#
#     Файл скачиваем кусками размером, заданным в переменной size. При скачивании файла изменяем прогресс-бар.
#     """
#     size = 1024 * 128
#     i = 0
#     fsize = int(res.headers['content-length'])
#     signals.file_name.emit(os.path.basename(file_dest))
#     signals.start_download.emit(int(fsize))
#     with open(file_dest, 'wb') as f:
#         try:
#             chunk = res.raw.read(size)
#             while chunk:
#                 f.write(chunk)
#                 i += size
#                 signals.progress.emit(i)
#                 chunk = res.raw.read(size)
#         except Exception:
#             logger.exception('')
#             signals.done.emit(4)
#             return
#     signals.done.emit(2)


# noinspection PyUnboundLocalVariable
def get_from_opds(url, searchText=None):
    """Сделать запрос по ссылке

    Производится проверка - является ли ссылка файлом или страницей. Если по ссылке находится файл, то происходит
    загрузка файла.
    """
    user_agent = generate_user_agent(os='linux', navigator='chrome')
    if not PROXIES:
        generate_proxies()

    if not searchText:
        params = None
    else:
        params = dict(searchTerm=searchText)

    if CURRENT_PROXY:
        try:
            res = request('get', URL + url,
                          proxies={'http': CURRENT_PROXY['http'], 'https': CURRENT_PROXY['http']},
                          headers={'user-agent': user_agent}, params=params, stream=True, timeout=(10, 30),
                          verify=False)
            res.raise_for_status()
        except (exceptions.ConnectionError, exceptions.ConnectTimeout, exceptions.HTTPError):
            signals.change_proxy.emit(None)
            logger.exception('')
            raise RequestErr
    else:
        for proxy in PROXIES:
            try:
                res = request('get', URL + url, proxies=proxy, headers={'user-agent': user_agent}, params=params,
                              stream=True, timeout=(10, 30), verify=False)
                res.raise_for_status()
                signals.change_proxy.emit(PROXY_LIST.copy())
                CURRENT_PROXY.update(proxy)
                signals.connect_to_proxy.emit()
                break
            except (exceptions.ConnectTimeout, exceptions.ConnectionError, exceptions.HTTPError):
                PROXY_LIST.remove(proxy['http'])
                res = None
    if not res:
        logger.error('Ошибка соединения')
        raise RequestErr('ОШИБКА СОЕДИНЕНИЯ')

    if not is_file(res.headers):
        return res.content
    else:
        logger.error(f'{res.text}')
        raise RequestErr('Ошибка получения страницы')

    # file = get_file_name(res)
    # thread = Thread(target=download_file,
    #                 kwargs=dict(res=res, file_dest=file))
    # thread.start()
    # raise DownloadFile('Скачивание файла')
