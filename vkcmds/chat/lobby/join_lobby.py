import time
import ranks
from vkcommands import VKCommand

CLOSED = ['открытое', 'закрытое']
GAMESTATUSPLAYING = ["game_playing", "game_paused"]
MAXLOBBIES = 1
MINPLAYERS = 2
MAXPLAYERS = 16  # четное


class Roulette(VKCommand):
    def __init__(self, kristy):
        VKCommand.__init__(self, kristy,
                           label='лобби>',
                           desc='Войти в лобби',
                           usage='!лобби>',
                           min_rank=ranks.Rank.PRO)

    def execute(self, chat, peer, sender, args=None, attachments=None):
        if self.kristy.check_user_lobby(chat, sender):
            self.kristy.send(peer, 'Вы уже в лобби')
            return

        if self.kristy.lobby[chat]["closed"] == 'закрытое' and sender not in self.kristy.lobby[chat]['invited']:
            self.kristy.send(peer, "Лобби является закрытым. Вам нужно приглашение от хоста.")
            return

        if len(self.kristy.lobby[chat]["players"]) >= self.kristy.lobby[chat]['max_players']:
            self.kristy.send(peer, "Лобби переполнено")
            return

        if sender in self.kristy.lobby[chat]["kicked"]:
            self.kristy.send(peer, "Вас кикнули из лобби. 😥")
            return

        self.kristy.lobby[chat]["players"].append(sender)
        users_vk = self.kristy.vk.users.get(user_ids=self.kristy.lobby[chat]["players"])
        names_users = []
        new_player_name = ""

        for user_vk in users_vk:
            if user_vk["id"] == sender:
                new_player_name = user_vk["first_name"] + " " + user_vk["last_name"]
            names_users.append(user_vk["first_name"] + " " + user_vk["last_name"])

        self.kristy.lobby[chat]["time_active"] = time.time() // 60
        self.kristy.send(peer, "В лобби новый игрок: {0}. \n"
                               "Все игроки ({1}): \n• {2}".format(new_player_name,
                                                                  str(len(self.kristy.lobby[chat]["players"]))
                                                                  + '/'
                                                                  + str(self.kristy.lobby[chat]['max_players']),
                                                                  ' \n• '.join(names_users)))
