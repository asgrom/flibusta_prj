import re
from datetime import datetime

from applogger import applogger
from jinja2 import Environment, FileSystemLoader

from . import BASE_DIR

logger = applogger.get_logger(__name__, __file__)

css = 'css/style.css'


def _is_auth_bio(text):
    """Проверка тега id

    Если тег содержит 'tag:author:bio', то это биография писателя.
    """
    if re.search(r'tag:author:bio:', text):
        return True
    else:
        return False


def _is_book(text):
    """Проверка тега id

    Если тег содержит 'tag:book:', то это описание книги.
    """
    if re.search(r'tag:book:', text):
        return True
    else:
        return False


# FileSystemLoader загружает шаблоны из файловой системы.
# Загрузчик получает путь до шаблонов как строку. Если нужно передать несколько путей расположения,
# то в него нужно передать список с путями.
# trim_blocks - удаляет символ новой строки после тега шаблона
env = Environment(loader=FileSystemLoader(BASE_DIR + '/templates'), autoescape=False, trim_blocks=True,
                  lstrip_blocks=True)

# регистрация тестов в окружении
env.tests['auth_bio'] = _is_auth_bio
env.tests['book'] = _is_book


# with open(os.path.join(BASE_DIR, 'css/style.css')) as f:
#     css = f.read()


def make_html_page(data):
    template = env.get_template(name='main.html')
    index_html = template.render(data=data, css=css, title=str(datetime.now()))
    return index_html


def make_test(data):
    template = env.get_template('test.html')
    test_html = template.render(data=data)
    return test_html


if __name__ == '__main__':
    pass
