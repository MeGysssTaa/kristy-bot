import ranks
from vkcommands import VKCommand
import os
import requests
from bs4 import BeautifulSoup
import re


class Roulette(VKCommand):
    def __init__(self, kristy):
        VKCommand.__init__(self, kristy,
                           label='картинка',
                           desc='Показывает случайную картинку',
                           min_rank=ranks.Rank.PRO)

    def execute(self, chat, peer, sender, args=None, attachments=None, fwd_messages=None):
        page_soup = BeautifulSoup(requests.get('https://avatarko.ru/random').text, 'html.parser')
        items = page_soup.find_all('div', class_='mb-2 img-thumbnail position-relative')
        image_url = 'https://avatarko.ru/' + items[0].find('img').get('src')
        image = requests.get(image_url).content
        with open('../tmp/picture{0}.png'.format(chat), 'wb') as handler:
            handler.write(image)
        uploads = self.kristy.vk_upload.photo_messages(photos="../tmp/picture{0}.png".format(chat))[0]
        quote_image = 'photo{0}_{1}'.format(uploads["owner_id"], uploads["id"])
        self.kristy.send(peer, "", quote_image)