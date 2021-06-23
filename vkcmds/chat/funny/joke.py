import json
import os

from bs4 import BeautifulSoup
from fuzzywuzzy import fuzz
import ranks
import keyboards
from PIL import Image, ImageDraw
import requests
from vkcommands import VKCommand


class ChooseChat(VKCommand):
    def __init__(self, kristy):
        VKCommand.__init__(self, kristy,
                           label='анекдот',
                           desc='Рассказывает анекдот (с сайта cast lots)')

    def execute(self, chat, peer, sender, args: str = None, attachments=None, fwd_messages=None):
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.106 Safari/537.36'}
        page_soup = BeautifulSoup(requests.get("https://www.anekdot.ru/random/anekdot/", headers=headers).text, 'html.parser')
        items = page_soup.find_all('div', class_='text')
        new_item = BeautifulSoup(str(items[0]).replace("<br/>", "\n"), features="html.parser")
        self.kristy.send(peer, new_item.get_text())
