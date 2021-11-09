import base64
import os

import requests

import ranks
from vkcommands import VKCommand


class Calc(VKCommand):
    def __init__(self, kristy):
        VKCommand.__init__(self, kristy,
                           label='calc',
                           desc='Калькулятор (ура)',
                           usage='!calc <выражение>',
                           min_args=1,
                           min_rank=ranks.Rank.PRO)

    def execute(self, chat, peer, sender, args=None, attachments=None, fwd_messages=None):
        msg = ' '.join(args)
        data = {'in[]': msg, 'trig': 'deg', 'p': 0, 's': 0}
        r = requests.post("https://web2.0calc.com/calc", data=data)
        response = r.json()
        if not response["results"]:
            self.kristy.send(peer, "Неверное выражение (надеюсь)")
            return
        response = response["results"][0]
        with open(f'./{chat}.png', 'wb') as file:
            file.write(base64.decodebytes(bytes(response["img64"], 'utf-8')))
        uploads = self.kristy.vk_upload.photo_messages(photos=f'./{chat}.png')[0]
        os.remove(f'./{chat}.png')
        self.kristy.send(peer, "", f'photo{uploads["owner_id"]}_{uploads["id"]}')
