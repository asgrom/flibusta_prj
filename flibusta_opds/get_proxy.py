from requests import request
from user_agent import generate_user_agent

from lxml import html as parser

user_agent = generate_user_agent(os='linux', navigator=['chrome', 'firefox'])

url = 'http://proxylist.hidemyass.com'


def get_html(url):
    """Получает страницу со списком прокси"""
    r = request('get', url, headers={'User-Agent': user_agent})
    print(r.encoding)
    return r.content


def html_parser(html):
    """Парсинг страницы со списком прокси"""
    root = parser.document_fromstring(html)


def main():
    print(user_agent)
    get_html('http://testsite.alex.org')


if __name__ == '__main__':
    main()
