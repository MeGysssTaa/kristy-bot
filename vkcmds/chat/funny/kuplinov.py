from vkcommands import VKCommand
from bs4 import BeautifulSoup
from random import randrange
import requests


KUPLINOV_QUOTES_PAGES = 4
KUPLINOV_QUOTES_PER_PAGE = 16
RAND_EMOJI_SET = ('☝', '🗿', '😉', '🤫', '😳', '🤡', '👌🏻', '💅🏻', '👀', '👊🏻', '👄', '🙂')


def _fetch_quote() -> str:
    quote_id = randrange(KUPLINOV_QUOTES_PAGES * KUPLINOV_QUOTES_PER_PAGE)
    quote_page = quote_id // KUPLINOV_QUOTES_PER_PAGE
    quote_index = quote_id // KUPLINOV_QUOTES_PAGES

    url = 'https://citaty.info/man/dmitrii-kuplinov?page=' + str(quote_page)
    page = requests.get(url).text
    bs = BeautifulSoup(page, features='html.parser')
    quotes = bs.find_all('div', class_='node__content')
    quote = quotes[quote_index]

    return quote.text.strip().split('Пояснение к цитате:')[0].split('\n\n')[0]


class KuplinovCommand(VKCommand):
    def __init__(self, kristy):
        VKCommand.__init__(self, kristy,
                           label='куплинов',
                           desc='Выдаёт цитату Куплинова')

    def execute(self, chat, peer, sender, args: str = None, attachments=None, fwd_messages=None):
        emoji = RAND_EMOJI_SET[randrange(len(RAND_EMOJI_SET))]
        text = _fetch_quote()
        self.kristy.send(peer, emoji + ' ' + text)
