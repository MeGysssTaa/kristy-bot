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
        r = requests.post("https://api.sbercloud.ru/v2/aicloud/gpt3", data={'question': text})
        answer = r.json()
        while answer["status"] != 'success':
            r = requests.post("https://api.sbercloud.ru/v2/aicloud/gpt3", data={'question': text})
            answer = r.json()
        self.kristy.send(peer, text + r.json()["data"])