import json
import random
import urllib.request

from fake_headers import Headers
import requests
from bs4 import BeautifulSoup

import ranks
from vkcommands import VKCommand

HEADERS_MY = [{'Accept': '*/*', 'Connection': 'keep-alive', 'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64; rv:52.5.3) Gecko/20100101 Firefox/52.5.3', 'Accept-Encoding': 'gzip, deflate, br', 'DNT': '1', 'Upgrade-Insecure-Requests': '1', 'Referer': 'https://google.com', 'Pragma': 'no-cache'},
              {'Accept': '*/*', 'Connection': 'keep-alive', 'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/69.0.3497.92 Safari/537.36', 'Accept-Encoding': 'gzip, deflate, br', 'Accept-Language': 'en-US;q=0.5,en;q=0.3', 'DNT': '1', 'Upgrade-Insecure-Requests': '1', 'Referer': 'https://google.com', 'Pragma': 'no-cache'},
              {'Accept': '*/*', 'Connection': 'keep-alive', 'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; WOW64; rv:60.5.2) Gecko/20100101 Firefox/60.5.2', 'Accept-Encoding': 'gzip, deflate, br', 'Accept-Language': 'en-US;q=0.5,en;q=0.3', 'DNT': '1', 'Upgrade-Insecure-Requests': '1', 'Referer': 'https://google.com', 'Pragma': 'no-cache'},
              {'Accept': '*/*', 'Connection': 'keep-alive', 'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/70.0.3538.77 Safari/537.36', 'Accept-Encoding': 'gzip, deflate, br', 'Accept-Language': 'en-US;q=0.5,en;q=0.3', 'Cache-Control': 'max-age=0', 'Pragma': 'no-cache'},
              {'Accept': '*/*', 'Connection': 'keep-alive', 'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:61.0.1) Gecko/20100101 Firefox/61.0.1', 'Accept-Encoding': 'gzip, deflate, br', 'Cache-Control': 'max-age=0', 'Upgrade-Insecure-Requests': '1', 'Referer': 'https://google.com', 'Pragma': 'no-cache'}]


class Roulette(VKCommand):
    def __init__(self, kristy):
        VKCommand.__init__(self, kristy,
                           label='картинка',
                           desc='Показывает картинку по тексту',
                           usage='!картинка <текст>',
                           min_args=1,
                           min_rank=ranks.Rank.PRO)

    def execute(self, chat, peer, sender, args=None, attachments=None, fwd_messages=None):
        if not args:
            self.kristy.send(peer, "Нету текста")
            return

        text = ' '.join(args)
        request = requests.get('https://yandex.ru/images/search',
                               params={"text": text,
                                       "nomisspell": 1,
                                       "noreask": 1})

        headers = {
            'Content-Type': 'application/json',
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 11_4) AppleWebKit/605.1.15 '
                          '(KHTML, like Gecko) Version/14.1.1 Safari/605.1.15',
            'Origin': 'https://yandex.ru',
            'Referer': 'https://yandex.ru/',
        }
        req = urllib.request.Request(request.url, headers=Headers().generate())
        response = urllib.request.urlopen(req)

        soup = BeautifulSoup(response.read().decode('utf8'), 'html.parser')
        items_place = soup.find('div', {"class": "serp-list"})
        items = items_place.find_all("div", {"class": "serp-item"})

        random_item = random.SystemRandom().choice(items)
        data = json.loads(random_item.get("data-bem"))
        image = data['serp-item']['img_href']
        photo = self.kristy.get_list_attachments([{"type": "photo",
                                                   "photo": {"sizes": [{"width": 400, "url": image}]}}], peer)
        self.kristy.send(peer, "", photo)
