import time
import ranks
import os
from vkcommands import VKCommand

CLOSED = ['открытое', 'закрытое']
GAMESTATUSPLAYING = ["game_playing", "game_paused"]
MAXLOBBIES = 1
MINPLAYERS = 2
MAXPLAYERS = 16  # четное


class Roulette(VKCommand):
    def __init__(self, kristy):
        VKCommand.__init__(self, kristy,
                           label='лобби<',
                           desc='Выйти из лобби',
                           usage='!лобби<',
                           min_rank=ranks.Rank.PRO)

    def execute(self, chat, peer, sender, args=None, attachments=None, fwd_messages=None):
        if not self.kristy.check_user_lobby(chat, sender):
            self.kristy.send(peer, "Вас нет в лобби")
            return
        if self.kristy.minigames[chat] and sender in self.kristy.minigames[chat]["players"]:
            self.kristy.send(peer, "Вы в игре, вы не можете покинуть лобби")
            return
        if len(self.kristy.lobby[chat]["players"]) > 1:
            if self.kristy.check_host_lobby(chat, sender):
                self.kristy.lobby[chat]["players"].remove(sender)
                host = self.kristy.lobby[chat]["players"][os.urandom(1)[0] % len(self.kristy.lobby[chat]["players"])]
                host_vk = self.kristy.vk.users.get(user_id=host)[0]
                self.kristy.lobby[chat]["host"] = host
                self.kristy.lobby[chat]["time_active"] = time.time() // 60
                self.kristy.send(peer, "Хост покидает лобби. Новый хост: {0}".format(host_vk["first_name"] + " " + host_vk["last_name"]))
            else:
                self.kristy.lobby[chat]["players"].remove(sender)
                self.kristy.send(peer, "Вы успешно покинули лобби")
        else:
            self.kristy.lobby.update({chat: {}})
            self.kristy.send(peer, "Последний игрок покинул лобби. Лобби удаляется...")


