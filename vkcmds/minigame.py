import ranks
import time
from vkcommands import VKCommand

GAMESTATUSALL = ["choose_game", "waiting_start", "playing_now"]
GAMESTATUSSELECTGAME = ["choose_game", "waiting_start"]


class Roulette(VKCommand):
    def __init__(self, kristy):
        VKCommand.__init__(self, kristy,
                           label='игра',
                           desc='Работа с лобби',
                           usage='!игра <команда> (старт, стоп, название_игры)',
                           min_rank=ranks.Rank.PRO,
                           min_args=1)

        self.MINIGAMES = {"фото": {'usage': '!игра фото <число раундом (10<=x<=30)>',
                                   'description': 'Вам будут показываться фотографии участников беседы. '
                                                  'Вы должны написать имя аккаунта этой фотографии (как в ВК), '
                                                  'то есть Петя, Пётр и Петр <- это три разных имени. Можно использовать заглавные или строчные буквы.',
                                   'min_args': 2,
                                   'select': self.select_game_photo}}

    def execute(self, chat, peer, sender, args=None, attachments=None):
        command = args[0].lower()
        if command == 'старт':
            self.start_game(chat, peer, sender, args)
        elif command == 'стоп':
            self.stop_game(chat, peer, sender)
        elif command in self.MINIGAMES:
            self.select_game(chat, peer, sender, args)
        else:
            self.kristy.send(peer, "Такой команды нет")

    def start_game(self, chat, peer, sender, args):
        name_host_lobby = self.kristy.get_user_created_lobby(chat, sender)
        if not name_host_lobby:
            self.kristy.send(peer, 'Вы не являетесь хостом какого-то лобби')
            return
        if self.kristy.lobby[chat][name_host_lobby]["status"] == "choose_game":
            self.kristy.send(peer, 'Выберите игру через !игра <название_игры>. \n'
                                   'Доступные: {0}'.format(', '.join(self.MINIGAMES.keys())))
            return
        if self.kristy.lobby[chat][name_host_lobby]["status"] == "playing_now":
            self.kristy.send(peer, 'В данный момент уже идёт игра.')
        self.kristy.manager.start_game(chat, peer, sender, self.kristy.lobby[chat][name_host_lobby]["minigame"]["name"])

    def stop_game(self, chat, peer, sender):
        pass

    def select_game(self, chat, peer, sender, args):
        name_host_lobby = self.kristy.get_user_created_lobby(chat, sender)
        minigame = args[0]
        if len(args) < self.MINIGAMES[minigame]['min_args']:
            self.kristy.send(peer, '⚠ Использование: \n' + self.MINIGAMES[minigame]['usage'])
        if not name_host_lobby:
            self.kristy.send(peer, 'Вы не являетесь хостом какого-то лобби')
            return
        if self.kristy.lobby[chat][name_host_lobby]["status"] not in GAMESTATUSSELECTGAME:
            self.kristy.send(peer, 'Сейчас нельзя выбрать мини-игру')
            return
        self.MINIGAMES[minigame]['select'](chat, peer, sender, args)

    def select_game_photo(self, chat, peer, sender, args):
        name_host_lobby = self.kristy.get_user_created_lobby(chat, sender)
        if not args[1].isdigit() or (args[1].isdigit() and not 1 <= int(args[1]) <= 30):
            self.kristy.send(peer, 'Неверный формат количества раундов (от 10 до 30)')
            return
        max_rounds = int(args[1])
        self.kristy.lobby[chat][name_host_lobby]['status'] = 'waiting_start'
        self.kristy.lobby[chat][name_host_lobby]['minigame'] = {
            "name": "фото",
            "settings": {
                "rounds_max": max_rounds
            }
        }
        self.kristy.lobby[chat][name_host_lobby]["time_active"] = time.time() // 60
        self.kristy.send(peer, "Успешно изменила мини-игру в лобби '{0}': \n"
                               "• Название: ФОТО \n"
                               "• Описание: {1} \n"
                               "• Число раундов: {2}".format(name_host_lobby,
                                                             self.MINIGAMES['фото']['description'],
                                                             str(max_rounds)))
