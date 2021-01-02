import ranks
from vkcommands import VKCommand
from PIL import Image, ImageDraw, ImageFont
import os
import requests
from bs4 import BeautifulSoup
import re


class Roulette(VKCommand):
    def __init__(self, kristy):
        VKCommand.__init__(self, kristy,
                           label='стикер',
                           desc='Показывает стикер',
                           min_rank=ranks.Rank.PRO)

    def execute(self, chat, peer, sender, args=None, attachments=None, fwd_messages=None):
        photo = Image.new("RGB", (600, 600), color=(255, 255, 255))
        draw = ImageDraw.Draw(photo)
        main_font = ImageFont.truetype("fonts/20219.ttf", 50)
        draw.text((300, 60, 1000, 100), "Этот стикер описывает вас", font=main_font, anchor='ms', fill=(0, 0, 0))

        page_soup = BeautifulSoup(requests.get('http://vkclub.su/ru/stickers/?sortby=date&page={0}'.format(os.urandom(1)[0] % 31)).text, 'html.parser')
        items = page_soup.find_all('div', class_='collections_list_item clickable_area')
        random_sticker = os.urandom(1)[0] % len(items)

        count = re.findall(r'\d+', items[random_sticker].find('div', class_='subtitle').string)[0]
        stiker_url = requests.get('http://vkclub.su{0}{1}'.format(items[random_sticker].find('div', class_='title').find('a').get('href'),
                                                                  str(os.urandom(1)[0] % len(count)).rjust(3, '0')))
        stiker_url_soup = BeautifulSoup(stiker_url.text, 'html.parser')
        stiker = requests.get('http://vkclub.su{0}'.format(stiker_url_soup.find('div', class_='column_center').find('img').get('src'))).content
        with open('../tmp/sticker{0}.png'.format(chat), 'wb') as handler:
            handler.write(stiker)

        sticker = Image.open('../tmp/sticker{0}.png'.format(chat)).convert("RGBA")
        sticker = sticker.resize((int(sticker.width * 0.78125), int(sticker.height * 0.78125)))
        photo.paste(sticker, (100, 130), sticker)
        photo.save("../tmp/quote{0}.jpg".format(chat))
        uploads = self.kristy.vk_upload.photo_messages(photos="../tmp/quote{0}.jpg".format(chat))[0]
        quote_image = 'photo{0}_{1}'.format(uploads["owner_id"], uploads["id"])
        self.kristy.send(peer, "", quote_image)
