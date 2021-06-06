import json
import os

import ranks
import keyboards
from vkcommands import VKCommand


class ChooseChat(VKCommand):
    def __init__(self, kristy):
        VKCommand.__init__(self, kristy,
                           label='рандом',
                           desc='Показывает рандомное голосовое, которое было в чате')

    def execute(self, chat, peer, sender, args=None, attachments=None, fwd_messages=None):
        voices = self.kristy.db.get_all_random_voices(chat)
        if len(voices) == 0:
            self.kristy.send(peer, "У вас нет ещё голосовых сообщений")
            return
        voice = voices[int(os.urandom(2).hex(), 16) % len(voices)]
        self.kristy.send(peer, "", voice)
