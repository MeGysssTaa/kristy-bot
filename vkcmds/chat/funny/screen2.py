import random
import re
import time

import requests
from bs4 import BeautifulSoup
from typing import List

from vkcommands import VKCommand

HEADERS = {
    'Content-Type': 'text/html; charset=utf-8',
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/98.0.4758.82 Safari/537.36'
}


class ChooseChat(VKCommand):
    def __init__(self, kristy):
        VKCommand.__init__(self, kristy,
                           label='скрин2',
                           usage='скрин2 [жанр1], [жанр2], ..., [жанрN]',
                           desc='Показывает скрин из аниме')

    def execute(self, chat, peer, sender, args: List[str] = None, attachments=None, fwd_messages=None):
        if args:
            args = ' '.join(args).split(',')
        args.sort()

        genres_url = "https://shikimori.one/api/genres"
        genres_json = requests.get(genres_url, headers=HEADERS).json()
        genres_json = {genre['russian'].lower(): str(genre['id']) for genre in genres_json if genre['kind'] == 'anime'}

        for arg in args:
            if arg.lower().strip() not in genres_json:
                self.kristy.send(peer, f"Не найден жанр: {arg.strip()}\n"
                                       f"Доступные жанры: {', '.join(sorted(list(genres_json.keys())))}")
                return
        genre_str = ','.join([genres_json[genre.lower().strip()] for genre in args])
        max_page = 100
        while True:
            random_page = random.SystemRandom().randint(1, max_page)
            random_anime = page_screens = genres = None
            url_animes = f"https://shikimori.one/api/animes?page={random_page}&limit=30&order=popularity&genre={genre_str}"
            page = requests.get(url_animes, headers=HEADERS).json()
            if len(page) == 0:
                max_page = random_page - 1
                if max_page == 0:
                    self.kristy.send(peer, "Для таких жанров не нашлось ни одного аниме, грустно(")
                    return
                time.sleep(1 / 5)
                continue
            random_anime = random.SystemRandom().choice(page)
            print(random_anime)
            time.sleep(1 / 5)
            url_anime_info = f"https://shikimori.one/api/animes/{random_anime['id']}"
            url_anime_screens = f"https://shikimori.one/api/animes/{random_anime['id']}/screenshots"
            page_info = requests.get(url_anime_info, headers=HEADERS).json()
            page_screens = requests.get(url_anime_screens, headers=HEADERS).json()

            genres = [genre["russian"].lower() for genre in page_info["genres"]]
            genres.sort()
            if page_screens:
                break
            time.sleep(1 / 5)
        random_screen = random.SystemRandom().choice(page_screens)
        self.kristy.anime[chat] = f"{random_anime['name']} / {random_anime['russian']} \n" \
                                  f"\n" \
                                  f"Жанры: {', '.join(genres)}"

        photo = self.kristy.get_list_attachments([{"type": "photo",
                                                   "photo": {"sizes": [{"width": 400, "url": f"https://shikimori.one{random_screen['original'].split('?')[0]}"}]}}], peer)[0]
        self.kristy.send(peer, "", attachment=photo)
