from bs4 import BeautifulSoup
import requests


class LinkParser:
    """
    Defines link parser from the web page
    """
    def __init__(self, link_template, main_selector, link_selector, link_property='href', **kwargs):
        """
        Constructor

        :param link_template: url of the page(could include %page_number% pattern).
        :param main_selector: CSS selector for main block where all links
            for parsing are stored.
        :param link_selector: CSS selector for all links that are required to parse
            inside the main block.
        :param link_property: (optional) Property of the link element, that contains
            url, "href" by default.
        :param page_from: (optional) Defines the page to start parsing from
            (1 if not specified).
            Used only if %page_number% in link_template specified.
        :param page_to: (optional) Defines the page to process parsing to
            (last page if not specified).
            Used only if %page_number% in link_template specified.
        :param: last_page_selector (optional) CSS selector to get the last page for
            page_to if it's not specified.
            Used only if %page_number% in link_template specified.
        :param: last_page_attribute (optional) Attribute of last page element to
            for get the page value from.
            Used only if %page_number% in link_template specified.
        """
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
            last_page_string = last_page_attribute[len(self.link[0]):len(self.link[1])] if len(self.link[1]) \
                else last_page_attribute[len(self.link[0]):]
            last_page = last_page_string.strip('/')
        else:
            last_page = last_page_attribute
        try:
            return int(last_page)
        except ValueError:
            raise ValueError('Unable to get last page number')

    def get_links(self):
        """
        Parsing the links using the parameters specified in
            the constructor.
        :return: :generator:`str` Generator of the parsed link strings.
        """
        for page in range(self.page_from, self.page_to + 1):
            r = self._get_request(page)
            soup = BeautifulSoup(r.content, 'lxml')
            main_section_soup = soup.select(self.main_selector)[0]
            for link_soup in main_section_soup.select(self.link_selector):
                link = link_soup[self.link_property]
                yield link


class ContentParser:
    """
        Defines content parser from the web page
    """
    def __init__(self, link, data_selector, title_selector, content_selector, exclude_selectors=None):
        """
        Constructor

        :param link: url of the page to parse.
        :param data_selector: CSS selector for main block where all the content is.
        :param title_selector: CSS selector for the title inside the main block.
        :param content_selector: CSS selector for the content inside the main block.
        :param exclude_selectors: (optional) CSS selectors that define elements to
            delete from the content during parsing.
        """
        self.link = link
        self.data_selector = data_selector
        self.title_selector = title_selector
        self.content_selector = content_selector
        self.exclude_selectors = exclude_selectors or []

    @staticmethod
    def _get_text_from_soup(soup):
        text = ''
        for e in soup.find_all(recursive=False):
            try:
                text += e.text.strip()
                if e.name == 'br' or e.name == 'p':
                    text += '\n'
            except AttributeError:
                pass
        return text.strip()

    def get_data(self):
        """
        Parsing the information using the parameters specified in
            the constructor.
        :return: dict: Dictionary with "title" and "content" keys.
        """
        r = requests.get(self.link)
        soup = BeautifulSoup(r.content, 'lxml')
        data_soup = soup.select(self.data_selector)[0]
        title = data_soup.select(self.title_selector)[0].text.strip()
        content_soup = data_soup.select(self.content_selector)[0]
        for data_exclude_selector in self.exclude_selectors:
            for element in content_soup.select(data_exclude_selector):
                element.decompose()
        content = ContentParser._get_text_from_soup(content_soup)
        return {
            'title': title,
            'content': content,
        }
