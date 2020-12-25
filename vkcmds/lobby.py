import os
import re
import time
import ranks
from vkcommands import VKCommand

CLOSED = ['открытое', 'закрытое']
GAMESTATUSPLAYING = ["playing_now"]
MAXLOBBYS = 1
MINPLAYERS = 2
MAXPLAYERS = 16


class Roulette(VKCommand):
    def __init__(self, kristy):
        VKCommand.__init__(self, kristy,
                           label='лобби',
                           desc='Работа с лобби',
                           usage='!лобби <команда> (создать, удалить, подключиться, отключиться, добавить, кикнуть)',
                           min_rank=ranks.Rank.PRO,
                           min_args=1)

    def execute(self, chat, peer, sender, args=None, attachments=None):
        command = args[0].lower()
        if command == 'создать':
            self.create_lobby(chat, peer, sender, args)
        elif command == 'удалить':
            self.remove_lobby(chat, peer, sender)
        elif command == 'войти':
            self.connect_to_lobby(chat, peer, sender, args)
        elif command == 'выйти':
            self.disconnect_from_lobby(chat, peer, sender)
        elif command == 'пригласить':
            self.invite_players(chat, peer, sender, args)
        elif command == 'кикнуть':
            self.kick_players(chat, peer, sender, args)
        elif command == 'все':
            self.view_lobby(chat, peer)
        else:
            self.kristy.send(peer, "Такой команды нет")

    def create_lobby(self, chat, peer, sender, args):
        usage = '!лобби создать <название_комнаты> <{0}> <количество участников ({1}<=x<={2})>'.format('/'.join(CLOSED), MINPLAYERS, MAXPLAYERS)
        if len(args) < 4:
            self.kristy.send(peer, '⚠ Использование: \n' + usage)
            return
        name_lobby = args[1]
        name_player_name = self.kristy.get_user_lobby(chat, sender)
        if name_player_name:
            self.kristy.send(peer, 'Вы уже находитесь в лобби: {0}'.format(name_player_name))
            return

        if args[2] not in CLOSED:
            self.kristy.send(peer, 'Нету такого статуса лобби. Доступные: {0}'.format(', '.join(CLOSED)))
            return
        closed = args[2]

        if not args[3].isdigit() or (args[3].isdigit() and not MINPLAYERS <= int(args[3]) <= MAXPLAYERS):
            self.kristy.send(peer, 'Неверный формат количества участник (целое число от {0} до {1})'.format(MINPLAYERS, MAXPLAYERS))
            return
        max_players = int(args[3])
        if len(self.kristy.lobby[chat]) >= MAXLOBBYS:
            self.kristy.send(peer, 'Уже создано максимальное количество лобби')
            return

        if name_lobby in self.kristy.lobby[chat]:
            self.kristy.send(peer, 'Лобби с таким названием уже существует')
            return

        if name_lobby in self.kristy.minigames[chat]:
            self.kristy.send(peer, 'Под таким названием сейчас идёт игра. Подождите пока она закончится')
            return

        self.kristy.lobby[chat].update({name_lobby: {"host": sender,
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
                               '💾 Название: {0} \n'
                               '😎 Хост: {1} \n'
                               '{2} Статус: {3} \n'
                               '👥 Количество мест: {4} \n \n'
                               '💡 Чтобы войти используйте: !лобби войти {0}'.format(name_lobby, sender_name, '✅' if closed == 'открытое' else '⛔', closed, max_players))

    def remove_lobby(self, chat, peer, sender):
        usage = '!лобби удалиль'
        name_host_lobby = self.kristy.get_user_created_lobby(chat, sender)
        if not name_host_lobby:
            self.kristy.send(peer, 'Вы не являетесь хостом какого-то лобби')
            return
        if self.kristy.lobby[chat][name_host_lobby]["status"] in GAMESTATUSPLAYING:
            self.kristy.send(peer, "В данный момент идёт игра, поэтому нельзя удалить лобби '{0}'".format(name_host_lobby))
            return
        self.kristy.lobby[chat].remove(name_host_lobby)
        self.kristy.send(peer, "Лобби '{0}' успешно удалено".format(name_host_lobby))

    def connect_to_lobby(self, chat, peer, sender, args):
        usage = '!лобби подключиться <название_комнаты>'

        if len(args) < 2:
            self.kristy.send(peer, '⚠ Использование: \n' + usage)
            return
        name_player_name = self.kristy.get_user_lobby(chat, sender)
        if name_player_name:
            self.kristy.send(peer, 'Вы уже находитесь в лобби: {0}'.format(name_player_name))
            return

        name_player_lobby = args[1]
        if name_player_lobby not in self.kristy.lobby[chat]:
            self.kristy.send(peer, "Лобби с таким именем '{0}' нет".format(name_player_lobby))
            return

        if self.kristy.lobby[chat][name_player_lobby]["closed"] == 'закрытое' and sender not in self.kristy.lobby[chat][name_player_lobby]['invited']:
            self.kristy.send(peer, "Лобби '{0}' является закрытым. Вам нужно приглашение от хоста.".format(name_player_lobby))
            return
        if len(self.kristy.lobby[chat][name_player_lobby]["players"]) >= self.kristy.lobby[chat][name_player_lobby]['max_players']:
            self.kristy.send(peer, "Лобби '{0}' переполнено".format(name_player_lobby))
            return
        print(self.kristy.lobby[chat][name_player_lobby])
        if sender in self.kristy.lobby[chat][name_player_lobby]["kicked"]:
            self.kristy.send(peer, "Вас кикнули из лобби '{0}'".format(name_player_lobby))
            return
        self.kristy.lobby[chat][name_player_lobby]["players"].append(sender)
        users_vk = self.kristy.vk.users.get(user_ids=self.kristy.lobby[chat][name_player_lobby]["players"])
        names_users = []
        new_player_name = ""

        for user_vk in users_vk:
            if user_vk["id"] == sender:
                new_player_name = user_vk["first_name"] + " " + user_vk["last_name"]
            names_users.append(user_vk["first_name"] + " " + user_vk["last_name"])
        self.kristy.lobby[chat][name_player_lobby]["time_active"] = time.time() // 60
        self.kristy.send(peer, "В лобби '{0}' новый игрок {1}. \n"
                               "Все игроки ({2}): \n• {3}".format(name_player_lobby,
                                                                  new_player_name,
                                                                  str(len(self.kristy.lobby[chat][name_player_lobby]["players"]))
                                                                  + '/'
                                                                  + str(self.kristy.lobby[chat][name_player_lobby]['max_players']),
                                                                  ' \n• '.join(names_users)))

    def disconnect_from_lobby(self, chat, peer, sender):
        usage = '!лобби отключиться'
        name_host_lobby = self.kristy.get_user_created_lobby(chat, sender)
        if name_host_lobby:
            self.kristy.send(peer, "Вы не можете покинуть лобби '{0}', так как являетесь его хостом. \n"
                                   "Вы можете его удалить через !лобби удалить")
            return
        name_player_lobby = self.kristy.get_user_lobby(chat, sender)
        if not name_player_lobby:
            self.kristy.send(peer, "Вас нет ни в каком лобби")
            return
        if self.kristy.lobby[chat][name_player_lobby]["status"] in GAMESTATUSPLAYING:
            self.kristy.send(peer, "В данный момент идёт игра, поэтому нельзя покинуть лобби '{0}'".format(name_host_lobby))
            return
        self.kristy.lobby[chat][name_player_lobby]["players"].remove(sender)
        self.kristy.lobby[chat][name_player_lobby]["time_active"] = time.time() // 60
        self.kristy.send(peer, "Вы успешно покинули  '{0}'".format(name_player_lobby))

    def invite_players(self, chat, peer, sender, args):
        usage = '!лобби пригласить <@ участники>'
        if len(args) < 2:
            self.kristy.send(peer, '⚠ Использование: \n' + usage)
            return
        name_host_lobby = self.kristy.get_user_created_lobby(chat, sender)
        if not name_host_lobby:
            self.kristy.send(peer, 'Вы не являетесь хостом какого-то лобби')
            return
        players = re.findall(r'\[id(\d+)\|[^]]+]', ' '.join(args[1:]))
        players = [int(player) for player in players]
        if not players:
            self.kristy.send(peer, "Вы не указали новых игроков через @")
            return
        members_chat = self.kristy.db.get_users(chat)
        players_not_found = list(set(players) - set(members_chat))
        players_invited = list(set(players) - set(players_not_found) - set(self.kristy.lobby[chat][name_host_lobby]["players"]) - set(self.kristy.lobby[chat][name_host_lobby]["invited"]))
        if not players_invited:
            self.kristy.send(peer, "Новые игроки не приглашены. \n"
                                   "Их нет в беседе, либо они уже в лобби '{0}', либо уже приглашены.".format(name_host_lobby))
            return
        for player in players_invited:
            self.kristy.lobby[chat][name_host_lobby]["invited"].append(player)
            if player in self.kristy.lobby[chat][name_host_lobby]["kicked"]:
                self.kristy.lobby[chat][name_host_lobby]["kicked"].remove(player)
        all_players_vk = self.kristy.vk.users.get(user_ids=players_invited)

        players = [player["first_name"] + ' ' + player["last_name"] for player in all_players_vk if player["id"] in players_invited]
        self.kristy.lobby[chat][name_host_lobby]["time_active"] = time.time() // 60
        self.kristy.send(peer, "В лобби '{0}' были приглашены: \n• {1}".format(name_host_lobby, ' \n• '.join(players)))

    def kick_players(self, chat, peer, sender, args):
        usage = '!лобби кикнуть <@ участники>'
        if len(args) < 2:
            self.kristy.send(peer, '⚠ Использование: \n' + usage)
            return
        name_host_lobby = self.kristy.get_user_created_lobby(chat, sender)
        if not name_host_lobby:
            self.kristy.send(peer, 'Вы не являетесь хостом какого-то лобби')
            return
        players = re.findall(r'\[id(\d+)\|[^]]+]', ' '.join(args[1:]))
        players = [int(player) for player in players]
        if not players:
            self.kristy.send(peer, "Вы не указали игроков, которых нужно кикнуть, через @")
            return
        members_chat = self.kristy.db.get_users(chat)
        players_not_in_lobby = list(set(self.kristy.lobby[chat][name_host_lobby]["players"]) - (set(players) - (set(players) - set(members_chat))))
        players_in_lobby = list(set(self.kristy.lobby[chat][name_host_lobby]["players"]) - set(players_not_in_lobby) - {sender})

        if not players_in_lobby:
            self.kristy.send(peer, "Никто не был кикнут. \n"
                                   "Возможно их нет в беседе или нет в лобби '{0}', либо вы хотели кикнуть себя".format(name_host_lobby))
            return

        for player in players_in_lobby:
            self.kristy.lobby[chat][name_host_lobby]["players"].remove(player)
            self.kristy.lobby[chat][name_host_lobby]["kicked"].append(player)
            if player in self.kristy.lobby[chat][name_host_lobby]["invited"]:
                self.kristy.lobby[chat][name_host_lobby]["invited"].remove(player)

        all_players_vk = self.kristy.vk.users.get(user_ids=players_in_lobby + self.kristy.lobby[chat][name_host_lobby]["players"])

        players = [player["first_name"] + ' ' + player["last_name"] for player in all_players_vk if player["id"] in players_in_lobby]
        players_names = [player["first_name"] + ' ' + player["last_name"] for player in all_players_vk if player["id"] not in players_in_lobby]
        self.kristy.lobby[chat][name_host_lobby]["time_active"] = time.time() // 60
        self.kristy.send(peer, "Из лобби '{0}' были кикнуты ({1}). \n"
                               "Все игроки ({2}): \n• {3}".format(name_host_lobby,
                                                                  ', '.join(players),
                                                                  str(len(self.kristy.lobby[chat][name_host_lobby]["players"]))
                                                                  + '/'
                                                                  + str(self.kristy.lobby[chat][name_host_lobby]['max_players']),
                                                                  ' \n• '.join(players_names)))
        pass

    def view_lobby(self, chat, peer):
        response = ''
        if not self.kristy.lobby[chat]:
            self.kristy.send(peer, "В чате нет активных лобби")
            return
        for number, name_lobby in enumerate(self.kristy.lobby[chat]):
            response += "{0}. {1} - {2} ({3}) \n".format(str(number + 1),
                                                         name_lobby,
                                                         self.kristy.lobby[chat][name_lobby]["closed"],
                                                         str(len(self.kristy.lobby[chat][name_lobby]["players"]))
                                                         + '/'
                                                         + str(self.kristy.lobby[chat][name_lobby]['max_players'])
                                                         )
        self.kristy.send(peer, response)
        pass
