import time
import ranks
import re
from vkcommands import VKCommand

CLOSED = ['открытое', 'закрытое']
GAMESTATUSPLAYING = ["game_playing", "game_paused"]
MAXLOBBIES = 1
MINPLAYERS = 2
MAXPLAYERS = 16  # четное


class Roulette(VKCommand):
    def __init__(self, kristy):
        VKCommand.__init__(self, kristy,
                           label='лобби!',
                           desc='Кикает из лобби игроков.',
                           usage='!лобби! <@ участников>',
                           min_rank=ranks.Rank.PRO,
                           min_args=1)

    def execute(self, chat, peer, sender, args=None, attachments=None, fwd_messages=None):
        if not self.kristy.check_host_lobby(chat, sender):
            self.kristy.send(peer, 'Вы не хост')
            return
        players = re.findall(r'\[id(\d+)\|[^]]+]', ' '.join(args[1:]))
        players = [int(player) for player in players]
        if not players:
            self.kristy.send(peer, "Вы не указали игроков, которых нужно кикнуть, через @")
            return
        members_chat = self.kristy.db.get_users(chat)
        players_not_in_lobby = list(set(self.kristy.lobby[chat]["players"]) - (set(players) - (set(players) - set(members_chat))))
        players_in_lobby = list(set(self.kristy.lobby[chat]["players"]) - set(players_not_in_lobby) - {sender})

        if not players_in_lobby:
            self.kristy.send(peer, "Никто не был кикнут. \n"
                                   "Возможно их нет в беседе, либо их нет в лобби, либо вы хотели кикнуть себя")
            return

        for player in players_in_lobby:
            self.kristy.lobby[chat]["players"].remove(player)
            self.kristy.lobby[chat]["kicked"].append(player)
            if player in self.kristy.lobby[chat]["invited"]:
                self.kristy.lobby[chat]["invited"].remove(player)

        all_players_vk = self.kristy.vk.users.get(user_ids=players_in_lobby + self.kristy.lobby[chat]["players"])

        players = [player["first_name"] + ' ' + player["last_name"] for player in all_players_vk if player["id"] in players_in_lobby]
        players_names = [player["first_name"] + ' ' + player["last_name"] for player in all_players_vk if player["id"] not in players_in_lobby]
        self.kristy.lobby[chat]["time_active"] = time.time() // 60
        self.kristy.send(peer, "Из лобби были кикнуты: {0}. \n"
                               "Все игроки ({1}): \n• {2}".format(', '.join(players),
                                                                  str(len(self.kristy.lobby[chat]["players"]))
                                                                  + '/'
                                                                  + str(self.kristy.lobby[chat]['max_players']),
                                                                  ' \n• '.join(players_names)))