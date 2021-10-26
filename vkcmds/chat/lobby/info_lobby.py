import time
import ranks
import re
from vkcommands import VKCommand

CLOSED = ['открытое', 'закрытое']
GAMESTATUSPLAYING = ["game_playing", "game_paused"]
MINPLAYERS = 2
MAXPLAYERS = 16  # четное


class Roulette(VKCommand):
    def __init__(self, kristy):
        VKCommand.__init__(self, kristy,
                           label='лобби?',
                           desc='Показывает информацию о лобби',
                           usage='!лобби?',
                           min_rank=ranks.Rank.PRO)

    def execute(self, chat, peer, sender, args=None, attachments=None, fwd_messages=None):
        if not self.kristy.lobby[chat]:
            self.kristy.send(peer, "Нет активного лобби")
            return
        players_vk = self.kristy.vk.users.get(user_ids=self.kristy.lobby[chat]["players"])
        players = [player["first_name"] + " " + player["last_name"] for player in players_vk]
        self.kristy.send(peer, "Игроки в лобби ({0}): \n• {1}".format(str(len(self.kristy.lobby[chat]["players"]))
                                                                      + '/'
                                                                      + str(self.kristy.lobby[chat]['max_players']),
                                                                      ' \n• '.join(players)))
