import json
import os
import random

from bs4 import BeautifulSoup
from fuzzywuzzy import fuzz
import ranks
import keyboards
from PIL import Image, ImageDraw
import requests
from vkcommands import VKCommand

MIN_PAGE = 0
MAX_PAGE = 35


class ChooseChat(VKCommand):
    def __init__(self, kristy):
        VKCommand.__init__(self, kristy,
                           label='анекдот',
                           desc='Рассказывает анекдот (с сайта cast lots)')

    def execute(self, chat, peer, sender, args: str = None, attachments=None, fwd_messages=None):
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.106 Safari/537.36'}
        random_number = random.SystemRandom().randint(MIN_PAGE, MAX_PAGE)
        page_soup = BeautifulSoup(requests.get(f"https://anekdotov.net/ancomp/index-page-{random_number}.html", headers=headers).text, 'html.parser')
        items = page_soup.find_all('div', class_='anekdot')
        item = random.SystemRandom().choice(items)
        new_item = BeautifulSoup(str(item).replace("<br/>", "\n"), features="html.parser")
        print(new_item.get_text())
        self.kristy.send(peer, new_item.get_text())
