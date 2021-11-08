import time

from minigames_manager import Minigame

POLE_SIZES = [4, 6, 8]


class Cubes(Minigame):
    def __init__(self, kristy):
        Minigame.__init__(self, kristy,
                          label='ячейки',
                          rules='Игра похоже на игру Purple Place (Школа). '
                                'Вам будет показано поле с ячейками. '
                                'Если перевернуть ячейку, то там будет изображение. '
                                'Игроки по очереди переворачивают по 2 ячейки. '
                                'Если изображение на двух ячейках одинаковое, то этот игрок ходит ещё раз, иначе ход переход следующему. '
                                'Побеждает тот, кто больше всех найдёт одинаковые ячейки.',
                          usage=f'!игра стрельба <размер поля: {", ".join(str(POLE_SIZES))}>',
                          min_args=1)

    def select_game(self, chat, peer, sender, args):
        self.kristy.lobby[chat]['status'] = 'waiting_start'
        if not args[1].isdigit() or (args[1].isdigit() and int(args[1]) not in POLE_SIZES):
            self.kristy.send(peer, f'Неверный формат размера поля (доступные: {", ".join(POLE_SIZES)}).')
            return
        size_map = int(args[1])
        self.kristy.lobby[chat]['minigame'] = {
            "name": self.label,
            "size_map": size_map
        }
        self.kristy.lobby[chat]["time_active"] = time.time() // 60
        self.kristy.send(peer, "Успешно изменила мини-игру в лобби: \n"
                               "• Название: {0} \n"
                               "• Описание: {1} \n"
                               "• Размер: {2} \n".format(self.label.upper(),
                                                         self.rules,
                                                         size_map))

    def start_game(self, chat, peer, sender):

        pass
