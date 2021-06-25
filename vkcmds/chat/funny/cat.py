import ranks
from vkcommands import VKCommand
import os
import requests
from bs4 import BeautifulSoup
import re


class Roulette(VKCommand):
    def __init__(self, kristy):
        VKCommand.__init__(self, kristy,
                           label='котик',
                           desc='Показывает случайную картинку котика')

    def execute(self, chat, peer, sender, args=None, attachments=None, fwd_messages=None):
        cat_image = requests.get('https://cataas.com/cat').content
        with open('../tmp/cat{0}.png'.format(chat), 'wb') as handler:
            handler.write(cat_image)
        uploads = self.kristy.vk_upload.photo_messages(photos="../tmp/cat{0}.png".format(chat))[0]
        os.remove("../tmp/cat{0}.png".format(chat))
        quote_image = 'photo{0}_{1}'.format(uploads["owner_id"], uploads["id"])
        self.kristy.send(peer, "", quote_image)