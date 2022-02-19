import random
import re
import pyshiki
import requests
from bs4 import BeautifulSoup

from vkcommands import VKCommand

HEADERS = {
    'Content-Type': 'text/html; charset=utf-8',
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/98.0.4758.82 Safari/537.36'
                  ''
}


class ChooseChat(VKCommand):
    def __init__(self, kristy):
        VKCommand.__init__(self, kristy,
                           label='скрин2',
                           desc='Показывает скрин из аниме')

    def execute(self, chat, peer, sender, args: str = None, attachments=None, fwd_messages=None):

        while True:
            random_page = random.SystemRandom().randint(1, 300)

            url_animes = f"https://shikimori.one/api/animes?page={random_page}&limit=50&order=popularity"

            page = requests.get(url_animes, headers=HEADERS).json()
            random_anime = random.SystemRandom().choice(page)

            url_anime_screens = f"https://shikimori.one/api/animes/{random_anime['id']}/screenshots"

            page_screens = requests.get(url_anime_screens, headers=HEADERS).json()
            if page_screens:
                break
        random_screen = random.SystemRandom().choice(page_screens)
        self.kristy.anime[chat] = f"{random_anime['name']} / {random_anime['russian']}"

        photo = self.kristy.get_list_attachments([{"type": "photo",
                                                   "photo": {"sizes": [{"width": 400, "url": f"https://shikimori.one{random_screen['original'].split('?')[0]}"}]}}], peer)[0]
        self.kristy.send(peer, "", attachment=photo)
