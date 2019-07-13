from lxml import html as parser
from requests import request, exceptions
from user_agent import generate_user_agent

from flibusta_opds.opds_requests import RequestErr

user_agent = generate_user_agent(os='linux', navigator=['chrome', 'firefox'])

url = 'http://proxylist.hidemyass.com'


def get_html(url):
    """Получает страницу со списком прокси"""
    try:
        r = request('get', url, headers={'User-Agent': user_agent}, timeout=(10, 30))
    except exceptions.RequestException:
        raise RequestErr('Ошибка получения страницы со списком прокси')
    r.raise_for_status()
    return r.content


def html_parser(html):
    """Парсинг страницы со списком прокси"""
    root = parser.document_fromstring(html)


def main():
    html = ''
    try:
        html = get_html('http://testsite.alex.org/')
    except Exception as e:
        print(e)
    print(html)


if __name__ == '__main__':
    main()
