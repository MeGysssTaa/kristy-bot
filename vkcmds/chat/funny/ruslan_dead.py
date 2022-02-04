import requests

import ranks
from vkcommands import VKCommand


class Ruslan(VKCommand):
    def __init__(self, kristy):
        VKCommand.__init__(self, kristy,
                           label='русландед',
                           desc='Руслан дед, просто Руслан дед.',
                           usage='!русландед <текст>',
                           min_rank=ranks.Rank.PRO,
                           min_args=1)

    def execute(self, chat, peer, sender, args=None, attachments=None, fwd_messages=None):
        text = ' '.join(args)
        headers = {
            'Content-Type': 'application/json',
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 11_4) AppleWebKit/605.1.15 '
                          '(KHTML, like Gecko) Version/14.1.1 Safari/605.1.15',
            'Origin': 'https://russiannlp.github.io',
            'Referer': 'https://russiannlp.github.io/',
        }
        r = requests.post("https://api.aicloud.sbercloud.ru/public/v1/public_inference/gpt3/predict", json={'text': text}, headers=headers)
        answer = r.json()
        while 'predictions' not in answer:
            print(1)
            r = requests.post("https://api.aicloud.sbercloud.ru/public/v1/public_inference/gpt3/predict", json={'text': text}, headers=headers)
            answer = r.json()
        self.kristy.send(peer, answer["predictions"])