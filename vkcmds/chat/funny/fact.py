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
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/93.0.4577.82 Safari/537.36",
                   "X-Requested-With": "XMLHttpRequest"}
        r = requests.post("https://randstuff.ru/fact/generate/", headers=headers)
        answer = r.json()
        self.kristy.send(peer, answer["fact"]["text"])
