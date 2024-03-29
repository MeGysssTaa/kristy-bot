import json
import random

import requests
from bs4 import BeautifulSoup

import ranks
from vkcommands import VKCommand


class Picture(VKCommand):
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
        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 11_4) AppleWebKit/605.1.15 '
                          '(KHTML, like Gecko) Version/14.1.1 Safari/605.1.15'
        }
        request = requests.get('https://yandex.ru/images/search',
                               params={"text": text,
                                       "nomisspell": 1,
                                       "noreask": 1
                                       },
                               headers=headers)
        soup = BeautifulSoup(request.text, 'html.parser')
        try:
            items_place = soup.find('div', {"class": "serp-list"})

            items = items_place.find_all("div", {"class": "serp-item"})

            random_item = random.SystemRandom().choice(items)
            data = json.loads(random_item.get("data-bem"))
            image = data['serp-item']['img_href']
            photo = self.kristy.get_list_attachments([{"type": "photo",
                                                       "photo": {"sizes": [{"width": 400, "url": image}]}}], peer)
            self.kristy.send(peer, "", photo)
        except Exception:
            self.kristy.send(peer, "Перезарядка")
