from bs4 import BeautifulSoup
import requests


class LinkParser:
    def __init__(self, link_template, main_selector, link_selector, link_property='href', **kwargs):
        self.main_selector = main_selector
        self.link_selector = link_selector
        self.link_property = link_property
        if '%page_number%' in link_template:
            page_number_position = link_template.index('%page_number%')
            self.link = (link_template[:page_number_position], link_template[page_number_position + 13:])
            self.link_paged = True
        else:
            self.link = link_template
            self.link_paged = False
        self.page_from = kwargs.get('page_from', None)
        self.page_to = kwargs.get('page_to', None)
        if (self.page_from is not None or self.page_to is not None) and not self.link_paged:
            raise ValueError('Unable to find %page_number% pattern in link_template')
        self.last_page_selector = kwargs.get('last_page_selector', None)
        self.last_page_attribute = kwargs.get('last_page_attribute', 'href')
        if self.page_to is None and self.link_paged:
            if self.last_page_selector is None:
                raise ValueError('Unable to find last_page or last_page_selector attribute')
            self.page_to = self._get_last_page_number()
        self.page_from = self.page_from or 1
        self.page_to = self.page_to or 1
        if self.page_from > self.page_to:
            raise ValueError(f'Start page ({self.page_from}) should be less or equal to end page ({self.page_to})')

    def _get_request(self, page):
        url = f'{self.link[0]}{page}{self.link[1]}' if self.link_paged else self.link
        return requests.get(url)

    def _get_last_page_number(self):
        if not self.link_paged:
            return None

        r = self._get_request(1)
        soup = BeautifulSoup(r.content, 'lxml')
        last_page_soup = soup.select(self.last_page_selector)[0]
        last_page_attribute = last_page_soup[self.last_page_attribute]
        if last_page_attribute.startswith(self.link[0]) and last_page_attribute.endswith(self.link[1]):
            last_page_string = last_page_attribute[len(self.link[0]):len(self.link[1])] if len(self.link[1])\
                else last_page_attribute[len(self.link[0]):]
            last_page = last_page_string.strip('/')
        else:
            last_page = last_page_attribute
        try:
            return int(last_page)
        except ValueError:
            raise ValueError('Unable to get last page number')

    def get_links(self):
        print(self.page_from, self.page_to)
        for page in range(self.page_from, self.page_to + 1):
            r = self._get_request(page)
            soup = BeautifulSoup(r.content, 'lxml')
            main_section_soup = soup.select(self.main_selector)[0]
            for link_soup in main_section_soup.select(self.link_selector):
                link = link_soup[self.link_property]
                yield link
