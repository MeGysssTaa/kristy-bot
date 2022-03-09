import requests
from bs4 import BeautifulSoup

import ranks
from vkcommands import VKCommand


class Ruslan(VKCommand):
    def __init__(self, kristy):
        VKCommand.__init__(self, kristy,
                           label='что',
                           desc='Скажет, что изображено на картинке',
                           usage='!что <картинка>',
                           min_rank=ranks.Rank.PRO,
                           min_args=1)

    def execute(self, chat, peer, sender, args=None, attachments=None, fwd_messages=None):
        if not attachments or attachments[0]["type"] != 'photo':
            self.kristy.send(peer, "Нету фотографии")

        key = "3fdabd98ed01dd617bb39bb8899a70a2"
        max_photo_url = ""
        max_width = 0
        for photo in attachments[0]['photo']['sizes']:
            if max_width < photo['width']:
                max_width = photo['width']
                max_photo_url = photo['url']
        r = requests.post('https://api.imgbb.com/1/upload', params={"key": key, "image": max_photo_url})
        answer_api = r.json()
        url = f'https://yandex.ru/images/search?source=collections&rpt=imageview&url={answer_api["data"]["url"]}'
        soup = BeautifulSoup(requests.get(url).text, features='html.parser')
        similar = soup.find('section', class_='CbirItem CbirTags')\
                      .find('div', class_='Tags Tags_type_expandable Tags_view_buttons')\
                      .find('div').find_all('a')
        self.kristy.send(peer, f"На картинке изображено: {similar[0].find('span').text}")
