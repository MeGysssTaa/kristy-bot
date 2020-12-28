import time
import ranks
from vkcommands import VKCommand

CLOSED = ['открытое', 'закрытое']
GAMESTATUSPLAYING = ["game_playing", "game_paused"]
MINPLAYERS = 2
MAXPLAYERS = 16  # четное


class Roulette(VKCommand):
    def __init__(self, kristy):
        VKCommand.__init__(self, kristy,
                           label='лобби+',
                           desc='Создаёт лобби',
                           usage='!лобби+ [{0} (default: открытое)] '
                                 '[количество участников от {1} до {2} (default: {3})]'.format('/'.join(CLOSED),
                                                                                               MINPLAYERS,
                                                                                               MAXPLAYERS,
                                                                                               MAXPLAYERS // 2),
                           min_rank=ranks.Rank.PRO)

    def execute(self, chat, peer, sender, args=None, attachments=None):
        closed = args[0] if args else "открытое"
        max_players = args[1] if len(args) > 1 else str(MAXPLAYERS // 2)

        if self.kristy.lobby[chat]:
            self.kristy.send(peer, "Уже создано лобби")
            return

        if closed not in CLOSED:
            self.kristy.send(peer, 'Нету такого статуса лобби. Доступные: {0}'.format(', '.join(CLOSED)))
            return
        if not max_players.isdigit() or (max_players.isdigit() and not MINPLAYERS <= int(max_players) <= MAXPLAYERS):
            self.kristy.send(peer, 'Неверный формат количества участник (целое число от {0} до {1})'.format(MINPLAYERS, MAXPLAYERS))
            return
        max_players = int(max_players)

        self.kristy.lobby.update({chat: {"host": sender,
                                         "closed": closed,
                                         "status": "choose_game",
                                         'max_players': max_players,
                                         'time_active': time.time() // 60,
                                         'minigame': {},
                                         'players': [sender],
                                         'invited': [],
                                         'kicked': []}})

        name_data = self.kristy.vk.users.get(user_id=sender)[0]
        sender_name = name_data['first_name'] + ' ' + name_data['last_name']

        self.kristy.send(peer, 'Успешно создала лобби с такими параметрами: \n'
                               '😎 Хост: {0} \n'
                               '{1} Статус: {2} \n'
                               '👥 Количество мест: {3} \n \n'
                               '💡 Чтобы войти используйте: !лобби>'.format(sender_name, '✅' if closed == 'открытое' else '⛔', closed, max_players))
