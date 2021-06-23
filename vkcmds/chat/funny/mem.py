import requests
from bs4 import BeautifulSoup

from vkcommands import VKCommand


class ChooseChat(VKCommand):
    def __init__(self, kristy):
        VKCommand.__init__(self, kristy,
                           label='мем',
                           desc='Показывает мем')

    def execute(self, chat, peer, sender, args: str = None, attachments=None, fwd_messages=None):
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.106 Safari/537.36'}
        page_soup = BeautifulSoup(requests.get("https://www.anekdot.ru/random/mem/", headers=headers).text, 'html.parser')
        items = page_soup.find_all('div', class_='text')
        for item in items:
            if item.find('img'):
                image_url = item.find('img').get('src')
                image = requests.get(image_url).content
                with open('../tmp/picture{0}.png'.format(chat), 'wb') as handler:
                    handler.write(image)
                uploads = self.kristy.vk_upload.photo_messages(photos="../tmp/picture{0}.png".format(chat))[0]
                quote_image = 'photo{0}_{1}'.format(uploads["owner_id"], uploads["id"])
                self.kristy.send(peer, "", quote_image)
                return
        self.kristy.send(peer, "Не повезло(")
