import base64
import json
import urllib.request
import requests
import time
import random

import threading

import ranks
from vkcommands import VKCommand


class Ruslan(VKCommand):
    def __init__(self, kristy):
        VKCommand.__init__(self, kristy,
                           label='anime',
                           desc='Преобразует фотографию в аниме',
                           usage='!anime <фото>',
                           min_rank=ranks.Rank.PRO,
                           min_args=1)

    def execute(self, chat, peer, sender, args=None, attachments=None, fwd_messages=None):
        if not attachments or attachments[0]["type"] != 'photo':
            self.kristy.send(peer, "Нету фотографии")
            return

        max_photo_url = ""
        max_width = 0
        for photo in attachments[0]['photo']['sizes']:
            if max_width < photo['width']:
                max_width = photo['width']
                max_photo_url = photo['url']

        photo_content = requests.get(max_photo_url).content
        photo_in_text = base64.b64encode(photo_content).decode()

        threading.Thread(target=self.ez, name='verim', args=(peer, photo_in_text,)).start()

    def get_hex(self):
        return hex(int(65536 * (random.random() + 1)))[3:]

    def ez(self, peer, photo_in_text):

        headers = {
            'Content-Type': 'application/json',
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 11_4) AppleWebKit/605.1.15 '
                          '(KHTML, like Gecko) Version/14.1.1 Safari/605.1.15',
            'Origin': 'https://h5.tu.qq.com',
            'Referer': 'https://h5.tu.qq.com/',
        }
        url = 'https://ai.tu.qq.com/trpc.shadow_cv.ai_processor_cgi.AIProcessorCgi/Process'
        for i in range(15):
            my_hex = f'{self.get_hex()}{self.get_hex()}-{self.get_hex()}-{self.get_hex()}-{self.get_hex()}-{self.get_hex()}{self.get_hex()}{self.get_hex()}'
            payload = {"busiId": 'ai_painting_anime_entry',
                       "extra": "{\"face_rects\":[],\"version\":2,\"platform\":\"web\",\"data_report\":{\"parent_trace_id\":\"" + my_hex + "\",\"root_channel\":\"\",\"level\":0}}",
                       'images': [photo_in_text]}

            params = json.dumps(payload).encode('utf8')
            req = urllib.request.Request(url, data=params, headers=headers)
            response = urllib.request.urlopen(req)
            response_json = json.loads(response.read().decode('utf8'))

            if response_json['code'] != 0:
                time.sleep(1)
                continue

            for url in json.loads(response_json['extra'])['img_urls']:
                if '/share/' in url:
                    photo = self.kristy.get_list_attachments(
                        [{"type": "photo", "photo": {"sizes": [{"width": 400, "url": url}]}}],
                        peer
                    )[0]
                    self.kristy.send(peer, '', [photo])
                    return

        self.kristy.send(peer, "Возникла ошибка, попробуйте ещё раз через некоторое время")
