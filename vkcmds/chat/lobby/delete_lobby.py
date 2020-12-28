import ranks
from vkcommands import VKCommand

GAMESTATUSPLAYING = ["game_playing", "game_paused"]


class Roulette(VKCommand):
    def __init__(self, kristy):
        VKCommand.__init__(self, kristy,
                           label='лобби-',
                           desc='Удаляет лобби',
                           usage='!лобби-',
                           min_rank=ranks.Rank.PRO)

    def execute(self, chat, peer, sender, args=None, attachments=None):
        if not self.kristy.lobby[chat]:
            self.kristy.send(peer, "Нету активного лобби")
            return
        if not self.kristy.check_user_lobby(chat, sender):
            self.kristy.send(peer, 'Вы не хост лобби')
            return
        if self.kristy.lobby[chat]["status"] in GAMESTATUSPLAYING:
            self.kristy.send(peer, "В данный момент идёт игра, поэтому нельзя удалить лобби")
            return
        self.kristy.lobby.update({chat: {}})
        self.kristy.send(peer, "Лобби успешно удалено")
