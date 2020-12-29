import ranks
import time
from vkcommands import VKCommand
import threading

GAME_STATUS_ALL = ["choose_game", "waiting_start", "game_playing", "game_paused"]
GAME_STATUS_PLAYING = ["game_playing", "game_paused"]
GAME_STATUS_SELECT_GAME = ["choose_game", "waiting_start"]


class Minigame(VKCommand):
    def __init__(self, kristy):
        VKCommand.__init__(self, kristy,
                           label='игра',
                           desc='Работа с мини-играми',
                           usage='!игра <команда> (старт, стоп, пауза, название_игры)',
                           min_rank=ranks.Rank.PRO,
                           min_args=1)

    def execute(self, chat, peer, sender, args=None, attachments=None, fwd_messages=None):
        command = args[0].lower()
        if not self.kristy.lobby[chat]:
            self.kristy.send(peer, 'Нет активного лобби')
            return
        if not self.kristy.check_host_lobby(chat, sender):
            self.kristy.send(peer, 'Вы не хост')
            return
        if command == 'старт':
            self.start_game(chat, peer, sender)
        elif command == 'стоп':
            self.stop_game(chat, peer)
        elif command in self.kristy.game_manager.minigames:
            self.select_game(chat, peer, sender, args)
        else:
            self.kristy.send(peer, "Такой команды нет. \nДоступные мини-игры: {0}".format(', '.join(self.kristy.game_manager.minigames.keys())))

    def start_game(self, chat, peer, sender):
        if self.kristy.lobby[chat]["status"] == "choose_game":
            self.kristy.send(peer, 'Выберите игру через !игра <название_игры>. \n'
                                   'Доступные: {0}'.format(', '.join(self.kristy.game_manager.minigames.keys())))
            return
        if self.kristy.lobby[chat]["status"] in GAME_STATUS_PLAYING:
            self.kristy.send(peer, 'В данный момент уже идёт игра.')
            return
        threading.Thread(target=self.kristy.game_manager.minigames[self.kristy.lobby[chat]["minigame"]["name"]].start_game, args=(chat, peer, sender), daemon=True).start()

    def stop_game(self, chat, peer):
        if self.kristy.lobby[chat]["status"] not in GAME_STATUS_PLAYING:
            self.kristy.send(peer, 'В данный момент нет игры')
            return
        self.kristy.minigames.update({chat: {}})
        self.kristy.lobby[chat]["status"] = "waiting_start"
        self.kristy.lobby[chat]["time_active"] = time.time() // 60
        self.kristy.send(peer, "Текущая игра была прервана")

    def select_game(self, chat, peer, sender, args):
        minigame = args[0]
        if len(args) - 1 < self.kristy.game_manager.minigames[minigame].min_args:
            self.kristy.game_manager.minigames[minigame].print_usage(peer)
            return

        if self.kristy.lobby[chat]["status"] not in GAME_STATUS_SELECT_GAME:
            self.kristy.send(peer, 'Сейчас нельзя выбрать мини-игру')
            return

        self.kristy.game_manager.minigames[minigame].select_game(chat, peer, sender, args)
