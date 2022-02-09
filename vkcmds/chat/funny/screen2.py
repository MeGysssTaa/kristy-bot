import random
import re

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

    def name_anime(self, chat, url):
        page_info = requests.get(url, headers=HEADERS).text
        bs = BeautifulSoup(page_info, features='html.parser')
        name = bs.find('header', class_="head").find('h1').text
        self.kristy.anime[chat] = name

    def get_anime_url(self):
        random_page = random.SystemRandom().randint(1, 809)
        url_animes = f'https://shikimori.one/animes/page/{random_page}'
        page = requests.get(url_animes, headers=HEADERS).content
        bs = BeautifulSoup(page, features='html.parser')
        animes = bs.find_all('a', class_="cover anime-tooltip")
        return random.SystemRandom().choice(animes).get('href')

    def execute(self, chat, peer, sender, args: str = None, attachments=None, fwd_messages=None):
        while True:
            anime_url = self.get_anime_url()

            self.name_anime(chat, anime_url)

            page_resourses = requests.get(f'{anime_url}/resources', headers=HEADERS).text
            bs = BeautifulSoup(page_resourses, features='html.parser')
            try:
                screens = bs.find('div', class_="c-screenshots").find('div', class_='cc').find_all('a')
                break
            except Exception:
                pass
        anime_url = random.SystemRandom().choice(screens).get('href')
        photo = self.kristy.get_list_attachments([{"type": "photo", "photo": {"sizes": [{"width": 400, "url": anime_url}]}}], peer)[0]
        self.kristy.send(peer, "", attachment=photo)
