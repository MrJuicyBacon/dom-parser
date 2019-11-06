from dom_parser import LinkParser, ContentParser

link_template = "https://pasmi.ru/cat/news/page/%page_number%"
main_selector = '#main > div.entries > div.post-list'
link_selector = 'article > h1 > a'
link_property = 'href'

data_selector = 'article > div.entry-content'
data_title_selector = 'h1.entry-title'
data_content_selector = 'div.content'
data_exclude_selectors = ('figure', 'div.ad', 'script', '.wp-polls')

links = LinkParser(link_template, main_selector, link_selector, page_from=1,
                   last_page_selector='div.nav-links a.page-numbers:not(.next):nth-last-of-type(2)').get_links()
for link in links:
    data = ContentParser(link, data_selector, data_title_selector,
                         data_content_selector, data_exclude_selectors).get_data()
    print(data)
