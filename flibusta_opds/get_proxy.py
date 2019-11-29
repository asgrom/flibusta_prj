# На сайте hidemyna.me проводится проверка браузера в течение 5 секунд.
# Поэтому с помощью requests'a страницу заполучть невозможно.
# Пришлось использовать selenium

import time
import json

from lxml import html as parser
from requests import request, exceptions
from selenium import webdriver
from user_agent import generate_user_agent

from flibusta_opds.opds_requests import RequestErr
from flibusta_opds import proxy_json_file

USER_AGENT = generate_user_agent(os='linux', navigator=['chrome', 'firefox'])

# УРЛ запроса списка прокси с временем отклика не более 300 мс и страны исключая Россию и Украину
URL = 'https://hidemy.name/ru/proxy-list/?country=CZFRDEHKHURSSLSETHGB&maxtime=300&type=hs#list'

def get_html_with_selenium(url):
    """Получить страницу с прокси-серверами с помощью selenium

    Время ожидания загрузки страницы выставлено на 10 секунд, плюс выставил ожидание после еще 10 секунд.
    Браузер запускается в режиме 'невидимки' - т.е. окно браузера не открывается. Делается с помощью аргумента 'headles'

    В режиме невидимки не получилось получить список. Сайт воспринимает меня как бота.
    """
    # options = webdriver.ChromeOptions()
    # аргумент опций для запуска браузера без запуска окна
    # options.add_argument('headless')
    ######################################################

    driver = webdriver.Chrome()
    driver.implicitly_wait(10)
    driver.get(url)
    time.sleep(10)
    assert 'Прокси-листы' in driver.title
    # код страницы
    html = driver.page_source
    driver.close()
    return html


def get_html_with_request(url):
    """Получает страницу со списком прокси"""
    try:
        r = request('get', url, headers={'User-Agent': USER_AGENT}, timeout=(10, 30))
    except exceptions.RequestException:
        raise RequestErr('Ошибка получения страницы со списком прокси')
    r.raise_for_status()

    with open('proxy_list.html', 'wb') as f:
        f.write(r.content)

    return r.content


def html_parser(html):
    """Парсинг страницы со списком прокси"""
    proxy_list = []

    # with open('res/page.html', 'w') as f:
        # f.write(html)

    root = parser.document_fromstring(html)
    # строки содержащие прокси
    tr = root.xpath('//div[@class="table_block"]/table/tbody/tr')

    for i in tr:
        td = i.xpath('./td')
        proxy_list.append(':'.join([td[0].text.strip(), td[1].text.strip()]))

    with open(proxy_json_file, 'w') as f:
        json.dump([i.strip(':') for i in proxy_list], f, ensure_ascii=False, indent=2)

    return proxy_list


def get_proxy_list():
    try:
        html = get_html_with_selenium(URL)
    except Exception as e:
        raise RequestErr('Ошибка получения списка прокси-серверов')
    return html_parser(html)


if __name__ == '__main__':
    get_proxy_list()
