import json
import pprint
import random
import urllib.request

import requests

import ranks
from vkcommands import VKCommand


class Ruslan(VKCommand):
    def __init__(self, kristy):
        VKCommand.__init__(self, kristy,
                           label='руслан2',
                           desc='Руслан, просто Руслан.',
                           usage='!руслан2 <текст>',
                           min_rank=ranks.Rank.PRO,
                           min_args=1)

    def execute(self, chat, peer, sender, args=None, attachments=None, fwd_messages=None):
        text = ' '.join(args)
        headers = {
            'Content-Type': 'application/json',
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 11_4) AppleWebKit/605.1.15 '
                          '(KHTML, like Gecko) Version/14.1.1 Safari/605.1.15',
            'Origin': 'https://porfirevich.ru'
        }
        url = 'https://pelevin.gpt.dobro.ai/generate/'

        payload = {"prompt": text, "length": 150}
        r = requests.post(url, json=payload, headers=headers)
        try:
            answer_text = random.choice(r.json()["replies"])
        except Exception:
            self.kristy.send(peer, "Попробуйте ещё раз или используйте !русландед")
        text += answer_text

        self.kristy.send(peer, text)



