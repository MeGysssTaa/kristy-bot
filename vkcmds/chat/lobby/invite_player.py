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
                           label='лобби*',
                           desc='Приглашает в лобби игроков.',
                           usage='!лобби* <@ участники>',
                           min_rank=ranks.Rank.PRO,
                           min_args=1)

    def execute(self, chat, peer, sender, args=None, attachments=None):
        if not self.kristy.check_host_lobby(chat, sender):
            self.kristy.send(peer, 'Вы не хост')
            return
        players = re.findall(r'\[id(\d+)\|[^]]+]', ' '.join(args[1:]))
        players = [int(player) for player in players]
        if not players:
            self.kristy.send(peer, "Вы не указали новых игроков через @")
            return
        members_chat = self.kristy.db.get_users(chat)
        players_not_found = list(set(players) - set(members_chat))
        players_invited = list(set(players) - set(players_not_found) - set(self.kristy.lobby[chat]["players"]) - set(self.kristy.lobby[chat]["invited"]))
        if not players_invited:
            self.kristy.send(peer, "Новые игроки не приглашены. \n"
                                   "Их нет в беседе, либо они уже в лобби, либо уже приглашены.")
            return
        for player in players_invited:
            self.kristy.lobby[chat]["invited"].append(player)
            if player in self.kristy.lobby[chat]["kicked"]:
                self.kristy.lobby[chat]["kicked"].remove(player)
        all_players_vk = self.kristy.vk.users.get(user_ids=players_invited)

        players = [player["first_name"] + ' ' + player["last_name"] for player in all_players_vk if player["id"] in players_invited]
        self.kristy.lobby[chat]["time_active"] = time.time() // 60
        self.kristy.send(peer, "В лобби были приглашены: \n• {0}".format(' \n• '.join(players)))
