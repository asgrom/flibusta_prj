from applogger import applogger
from requests import request, exceptions
from user_agent import generate_user_agent

from . import PROXY_LIST, signals, CURRENT_PROXY


class RequestErr(Exception):
    pass


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
            return res.content
        except (exceptions.ConnectionError, exceptions.ConnectTimeout, exceptions.HTTPError, exceptions.ReadTimeout):
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
                return res.content
            except (exceptions.ConnectTimeout, exceptions.ConnectionError, exceptions.HTTPError, exceptions.ReadTimeout):
                PROXY_LIST.remove(proxy['http'])
                res = None
    if not res:
        logger.error('Ошибка соединения')
        raise RequestErr('ОШИБКА СОЕДИНЕНИЯ')
