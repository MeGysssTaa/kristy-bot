import json
import random
import urllib.request

import ranks
from vkcommands import VKCommand


class Anime(VKCommand):
    def __init__(self, kristy):
        VKCommand.__init__(self, kristy,
                           label='аниме',
                           desc='Нужно больше Аниме',
                           usage='!аниме',
                           min_rank=ranks.Rank.PRO)

    def execute(self, chat, peer, sender, args=None, attachments=None, fwd_messages=None):
        with open(r"./anime/anime.txt", "r") as file:
            animes_dict: dict = json.loads(file.read())
        self.kristy.send(peer, "", attachment=random.SystemRandom().choice(list(animes_dict.values())))


