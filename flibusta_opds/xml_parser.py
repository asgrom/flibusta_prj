from datetime import datetime as dt

from lxml import etree as et

from . import signals


class XMLError(Exception):
    pass


# пространсто имен по-умолчанию для парсинга
nsx = {'ns': 'http://www.w3.org/2005/Atom'}


def parser(fromfile=None, fromstr=None):
    data = {'entries': []}
    try:
        root = et.parse(fromfile).getroot() if fromfile else et.fromstring(fromstr)
        data.update(title=root.xpath('./ns:title/text()', namespaces=nsx)[0])
        data.update(id=root.xpath('./ns:id/text()', namespaces=nsx)[0])

        # ищем ссылки на следующую и предыдущую страницы, и если они есть, сохраняем их в словарь.
        nav_links = root.xpath('./ns:link[@rel="up" or @rel="next"]', namespaces=nsx)
        attrs = [(tag.xpath('@rel')[0], tag.xpath('@href')[0]) for tag in nav_links]
        data.update(dict(attrs))

        # разбираем файл по тегу entry
        for entry in root.xpath('./ns:entry', namespaces=nsx):
            # в блоке entry выдергиваем все ссылки с их атрибутами
            data_entry = {'links': [dict(i.attrib) for i in entry.xpath('./ns:link', namespaces=nsx)]}
            # разбираем сам блок entry
            data_entry.update(parse_entry(entry))
            data['entries'].append(data_entry)
        return data
    except et.XMLSyntaxError:
        signals.change_proxy.emit(None)
        raise XMLError(f'ОШИБКА ПАРСИНГА СТРАНИЦЫ\nПрокси сервер будет удален из списка.')


def parse_entry(chunk):
    """Парсит кусок переданных данных xml"""
    tags = chunk.xpath('./*[not(local-name()="link")]')
    dct = dict(category=list(), author=list())
    for tag in tags:
        tag_name = tag.xpath('local-name()')
        if tag_name == 'updated':
            dct[tag_name] = dt.astimezone(
                dt.fromisoformat(tag.xpath('text()')[0])).strftime(
                '%d-%m-%Y %H:%M:%S'
            )
        elif tag_name == 'category':
            dct[tag_name].append(tag.xpath('./@label')[0])
        elif tag_name == 'author':
            dct[tag_name].append(tag.xpath('./ns:name', namespaces=nsx)[0].text)
        else:
            dct[tag_name] = tag.text
    return dct


if __name__ == '__main__':
    pass
