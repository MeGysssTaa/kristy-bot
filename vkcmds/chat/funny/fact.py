import json
import os
from fuzzywuzzy import fuzz
import ranks
import keyboards
from PIL import Image, ImageDraw
import requests
from vkcommands import VKCommand


class ChooseChat(VKCommand):
    def __init__(self, kristy):
        VKCommand.__init__(self, kristy,
                           label='факт',
                           desc='Даёт факт (с сайта randstuff)')

    def execute(self, chat, peer, sender, args: str = None, attachments=None, fwd_messages=None):
        headers = {
            'Host': 'randstuff.ru',
            'Connection': 'keep-alive',
            'Content-Length': '0',
            'sec-ch-ua': '" Not;A Brand";v="99", "Google Chrome";v="91", "Chromium";v="91"',
            'Accept': 'application/json, text/javascript, */*; q=0.01',
            'X-Requested-With': 'XMLHttpRequest',
            'sec-ch-ua-mobile': '?0',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.106 Safari/537.36',
            'Origin': 'https://randstuff.ru',
            'Sec-Fetch-Site': 'same-origin',
            'Sec-Fetch-Mode': 'cors',
            'Sec-Fetch-Dest': 'empty',
            'Referer': 'https://randstuff.ru/fact/',
            'Accept-Encoding': 'gzip, deflate, br',
            'Accept-Language': 'ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7'}
        r = requests.post("https://randstuff.ru/fact/generate/", headers=headers)
        answer = r.json()
        self.kristy.send(peer, answer["fact"]["text"])
