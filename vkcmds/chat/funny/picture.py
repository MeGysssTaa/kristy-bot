import json
import random
from fake_headers import Headers
import requests
from bs4 import BeautifulSoup

import ranks
from vkcommands import VKCommand


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
                                       "noreask": 1},
                               headers=Headers(headers=True).generate())
        soup = BeautifulSoup(request.text, 'html.parser')
        items_place = soup.find('div', {"class": "serp-list"})
        self.kristy.send(233737645, items_place)
        items = items_place.find_all("div", {"class": "serp-item"})

        random_item = random.SystemRandom().choice(items)
        data = json.loads(random_item.get("data-bem"))
        image = data['serp-item']['img_href']
        photo = self.kristy.get_list_attachments([{"type": "photo",
                                                   "photo": {"sizes": [{"width": 400, "url": image}]}}], peer)
        self.kristy.send(peer, "", photo)
