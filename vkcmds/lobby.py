import os
import re
import time
import ranks
from vkcommands import VKCommand

MINIGAMES = ['фото']
STATUSES = ['открытое', 'закрытое']
MAXLOBBYS = 1
MINPLAYERS = 2
MAXPLAYERS = 8


class Roulette(VKCommand):
    def __init__(self, kristy):
        VKCommand.__init__(self, kristy,
                           label='лобби',
                           desc='Работа с лобби',
                           usage='!лобби <команда> (создать, удалить, подключиться, отключиться, добавить, кикнуть)',
                           min_rank=ranks.Rank.PRO)

    def execute(self, chat, peer, sender, args=None, attachments=None):
        command = args[0].lower()
        if chat not in self.kristy.lobby:
            self.kristy.lobby.update({chat: {}})
        if command == 'создать':
            self.create_lobby(chat, peer, sender, args)
        elif command == 'удалить':
            self.remove_lobby(chat, peer, sender)
        elif command == 'подключиться':
            self.connect_to_lobby(chat, peer, sender, args)
        elif command == 'отключиться':
            self.disconnect_from_lobby(chat, peer, sender)
        elif command == 'добавить':
            self.add_players(chat, peer, sender, args)
        elif command == 'кикнуть':
            self.kick_players(chat, peer, sender, args)
        elif command == 'все':
            self.view_lobby(chat, peer, sender)
        else:
            self.kristy.send(peer, "Такой команды нет")

    def create_lobby(self, chat, peer, sender, args):
        usage = '!лобби создать <название_комнаты> <{0}> <количество участников ({1}<=x<={2})>'.format('/'.join(STATUSES), MINPLAYERS, MAXPLAYERS)
        if len(args) < 4:
            self.kristy.send(peer, '⚠ Использование: \n' + usage)
            return
        name_lobby = args[1]
        if self.get_user_lobby(chat, sender):
            self.kristy.send(peer, 'Вы уже находитесь в лобби: {0}'.format(self.get_user_lobby(chat, sender)))
            return

        if args[2] not in STATUSES:
            self.kristy.send(peer, 'Нету такого статуса лобби. Доступные: {0}'.format(', '.join(STATUSES)))
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
        self.kristy.lobby[chat].update({name_lobby: {"host": sender,
                                                     "closed": closed,
                                                     "status": "select_game",
                                                     'max_players': max_players,
                                                     'time_active': time.time() // 60,
                                                     'minigame': {'players': []},
                                                     'players': [sender],
                                                     'kicked': []}})

        name_data = self.kristy.vk.users.get(user_id=sender)[0]
        sender_name = name_data['first_name'] + ' ' + name_data['last_name']

        self.kristy.send(peer, 'Успешно создала лобби с такими параметрами: \n'
                               '• Название: {0} \n'
                               '• Хост: {1} \n'
                               '• Статус: {2} \n'
                               '• Количество участников: {3}'.format(name_lobby, sender_name, closed, max_players))

    def remove_lobby(self, chat, peer, sender):
        usage = '!лобби удалиль'
        name_host_lobby = self.get_user_created_lobby(chat, sender)
        if not name_host_lobby:
            self.kristy.send(peer, 'Вы не являетесь хостом какого-то лобби')
        else:
            self.kristy.lobby[chat].pop(name_host_lobby)
            self.kristy.send(peer, "Лобби с названием '{0}' успешно удалено".format(name_host_lobby))

    def connect_to_lobby(self, chat, peer, sender, args):
        usage = '!лобби подключиться <название_комнаты>'

        if len(args) < 2:
            self.kristy.send(peer, '⚠ Использование: \n' + usage)
            return

        if self.get_user_lobby(chat, sender):
            self.kristy.send(peer, 'Вы уже находитесь в лобби: {0}'.format(self.get_user_lobby(chat, sender)))
            return

        name_player_lobby = args[1]
        if name_player_lobby not in self.kristy.lobby[chat]:
            self.kristy.send(peer, "Лобби с таким именем '{0}' нет".format(name_player_lobby))
            return

        if self.kristy.lobby[chat][name_player_lobby]["closed"] == 'закрытое':
            self.kristy.send(peer, "Лобби '{0}' является закрытым".format(name_player_lobby))
            return
        if len(self.kristy.lobby[chat][name_player_lobby]["players"]) >= self.kristy.lobby[chat][name_player_lobby]['max_players']:
            self.kristy.send(peer, "Лобби '{0}' переполнено".format(name_player_lobby))
            return
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
        self.kristy.send(peer, "В лобби '{0}' новый игрок {1}. \n"
                               "Все игроки ({2}): \n• {3}".format(name_player_lobby,
                                                                  new_player_name,
                                                                  str(len(self.kristy.lobby[chat][name_player_lobby]["players"]))
                                                                  + '/'
                                                                  + str(self.kristy.lobby[chat][name_player_lobby]['max_players']),
                                                                  ' \n• '.join(names_users)))

    def disconnect_from_lobby(self, chat, peer, sender):
        usage = '!лобби отключиться'
        name_host_lobby = self.get_user_created_lobby(chat, sender)
        if name_host_lobby:
            self.kristy.send(peer, "Вы не можете покинуть лобби '{0}', так как являетесь его хостом. \n"
                                   "Вы можете его удалить через !лобби удалить")
            return
        name_player_lobby = self.get_user_lobby(chat, sender)
        if not name_player_lobby:
            self.kristy.send(peer, "Вас нет ни в каком лобби")
            return
        self.kristy.lobby[chat][name_player_lobby]["players"].remove(sender)
        self.kristy.send(peer, "Вы успешно покинули  '{0}'".format(name_player_lobby))

    def add_players(self, chat, peer, sender, args):
        usage = '!лобби добавить <@ участники>'
        if len(args) < 2:
            self.kristy.send(peer, '⚠ Использование: \n' + usage)
            return
        name_host_lobby = self.get_user_created_lobby(chat, sender)
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
        players_joined = list(set(players) - set(players_not_found) - set(self.kristy.lobby[chat][name_host_lobby]["players"]))
        if not players_joined:
            self.kristy.send(peer, "Новые игроки не добавлены. \n"
                                   "Их нет в беседе, либо они уже в лобби '{0}'".format(name_host_lobby))
            return
        if len(players_joined) + len(self.kristy.lobby[chat][name_host_lobby]["players"]) > self.kristy.lobby[chat][name_host_lobby]['max_players']:
            self.kristy.send(peer, "В вашем лобби {0} недостаточно места для всех указаных игроков. \n"
                                   "Осталось: {1}".format(name_host_lobby,
                                                          str(self.kristy.lobby[chat][name_host_lobby]['max_players']
                                                              - len(self.kristy.lobby[chat][name_host_lobby]["players"]))))
            return
        for player in players_joined:
            self.kristy.lobby[chat][name_host_lobby]["players"].append(player)
            if player in self.kristy.lobby[chat][name_host_lobby]["kicked"]:
                self.kristy.lobby[chat][name_host_lobby]["kicked"].remove(player)
        all_players_vk = self.kristy.vk.users.get(user_ids=players_joined + self.kristy.lobby[chat][name_host_lobby]["players"])

        players = [player["first_name"] + ' ' + player["last_name"] for player in all_players_vk if player["id"] in players_joined]
        players_names = [player["first_name"] + ' ' + player["last_name"] for player in all_players_vk]
        self.kristy.send(peer, "В лобби '{0}' новые игроки ({1}). \n"
                               "Все игроки ({2}): \n• {3}".format(name_host_lobby,
                                                                  ' ,'.join(players),
                                                                  str(len(self.kristy.lobby[chat][name_host_lobby]["players"]))
                                                                  + '/'
                                                                  + str(self.kristy.lobby[chat][name_host_lobby]['max_players']),
                                                                  ' \n• '.join(players_names)))

    def kick_players(self, chat, peer, sender, args):
        usage = '!лобби кикнуть <@ участники>'
        if len(args) < 2:
            self.kristy.send(peer, '⚠ Использование: \n' + usage)
            return
        name_host_lobby = self.get_user_created_lobby(chat, sender)
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

        all_players_vk = self.kristy.vk.users.get(user_ids=players_in_lobby + self.kristy.lobby[chat][name_host_lobby]["players"])

        players = [player["first_name"] + ' ' + player["last_name"] for player in all_players_vk if player["id"] in players_in_lobby]
        players_names = [player["first_name"] + ' ' + player["last_name"] for player in all_players_vk]
        self.kristy.send(peer, "Из лобби '{0}' были кикнуты ({1}). \n"
                               "Все игроки ({2}): \n• {3}".format(name_host_lobby,
                                                                  ' ,'.join(players),
                                                                  str(len(self.kristy.lobby[chat][name_host_lobby]["players"]))
                                                                  + '/'
                                                                  + str(self.kristy.lobby[chat][name_host_lobby]['max_players']),
                                                                  ' \n• '.join(players_names)))
        pass

    def view_lobby(self, chat, peer, sender, args):
        pass

    def get_user_created_lobby(self, chat, sender):
        for name, lobby in self.kristy.lobby[chat].items():
            if lobby["host"] == sender:
                return name
        return ''

    def get_user_lobby(self, chat, sender):
        for name, lobby in self.kristy.lobby[chat].items():
            if sender in lobby["players"]:
                return name
        return ''
