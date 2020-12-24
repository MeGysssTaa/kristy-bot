import time
import threading
import os
import traceback

GAMES_ANSWERS = ['фото', 'статус', 'вопросы']


class Maneger:
    def __init__(self, kristy):
        self.kristy = kristy

        self.MINIGAMES = {'фото': {'correct': 'Владелец фотографии',
                                   'next': 'Следующая фотография',
                                   'get': self.get_photo},
                          'статус': {'correct': 'Это статус',
                                     'next': 'Следующий статус',
                                     'get': self.get_status}
                          }
        threading.Thread(target=self.check_active_lobby, name='check-lobby', daemon=True).start()
        GAMES_ANSWERS = {'фото': {'correct': 'Владелец фотографии',
                                  'next': 'Следующая фотография',
                                  'get': self.get_photo},
                         'статус': {'correct': 'Это статус',
                                    'next': 'Следующий статус',
                                    'get': self.get_status},
                         'вопросы': {'correct': 'Правильный ответ на вопрос',
                                     'next': 'Следущий вопрос'}}

    def check_active_lobby(self):
        while True:
            for chat in self.kristy.lobby:
                all_lobby_in_chat = list(self.kristy.lobby[chat].keys()).copy()
                for lobby in all_lobby_in_chat:
                    if self.kristy.lobby[chat][lobby]["time_active"] + 60 < time.time() // 60:
                        self.kristy.lobby[chat].pop(lobby)
                        if lobby in self.kristy.minigames[chat]:
                            self.kristy.minigames[chat].pop(lobby)
                        self.kristy.send(2E9 + chat, "Лобби '{0}' было удалено из-за неактивности.".format(lobby))

            time.sleep(60 - time.time() % 60)

    def start_game(self, chat, peer, sender, name):
        try:
            threading.Thread(target=self.start_game_choose_correct_answer, args=(chat, peer, sender, name,), daemon=True).start()
        except Exception:
            self.kristy.send(peer, traceback.format_exc(), ["photo-199300529_457239560"])
            traceback.print_exc()

    def check_game(self, chat, peer, sender, text):
        for minigame in self.kristy.minigames[chat]:
            if sender in self.kristy.minigames[chat][minigame]["players"]:
                name = self.kristy.minigames[chat][minigame]['name']
                break
        else:
            return
        try:
            if name in GAMES_ANSWERS:
                threading.Thread(target=self.game_choose_correct_answer, args=(chat, peer, sender, name, text,), daemon=True).start()
        except Exception:
            self.kristy.send(peer, traceback.format_exc(), ["photo-199300529_457239560"])
            traceback.print_exc()

    def start_game_choose_correct_answer(self, chat, peer, sender, name_game):
        name_host_lobby = self.kristy.get_user_created_lobby(chat, sender)
        self.kristy.lobby[chat][name_host_lobby]['status'] = 'playing_now'

        all_players_vk = self.kristy.vk.users.get(user_ids=self.kristy.lobby[chat][name_host_lobby]["players"])

        players = {}
        max_rounds = self.kristy.lobby[chat][name_host_lobby]['minigame']["settings"]["rounds_max"]
        for player in all_players_vk:
            players.update({player["id"]: {
                "name": player["first_name"] + " " + player["last_name"],
                "correct": 0
            }})

        self.kristy.send(peer, "Новая мини-игра: \n"
                               "• Лобби: {0} \n"
                               "• Мини-игра: {1} \n"
                               "• Раундов: {2} \n"
                               "• Игроки: \n"
                               "• • {3} \n"
                               "Начало через 10 секунд, приготовьтесь!".format(name_host_lobby,
                                                                               name_game.upper(),
                                                                               str(max_rounds),
                                                                               ' \n• • '.join([player["name"] for player in players.values()])))
        time_now = time.time() + 10
        answer, response, attachments = self.MINIGAMES[name_game]['get'](chat, peer)
        time.sleep(time_now - time.time())

        self.kristy.lobby[chat][name_host_lobby]['time_active'] = time.time() // 60
        if not answer:
            self.kristy.send(peer, "Ой-ой, похоже ответа нет")
            self.kristy.lobby[chat][name_host_lobby]['status'] = 'waiting_start'
            return

        self.kristy.minigames[chat].update({
            name_host_lobby: {
                'name': name_game,
                'players': players,
                'round': 1,
                'max_rounds': max_rounds,
                'answer': answer

            }
        })

        self.kristy.send(peer, "Игра началась. " + response, attachments)

    def game_choose_correct_answer(self, chat, peer, sender, name_game, text):
        name_user_lobby = self.kristy.get_user_lobby(chat, sender)
        if text.strip().lower() != self.kristy.minigames[chat][name_user_lobby]['answer'].strip().lower():
            return
        self.kristy.lobby[chat][name_user_lobby]['time_active'] = time.time() // 60
        response = '{0} отвечает правильно. {1}: {2} \n'.format(self.kristy.minigames[chat][name_user_lobby]["players"][sender]["name"],
                                                                self.MINIGAMES[name_game]['correct'],
                                                                self.kristy.minigames[chat][name_user_lobby]["answer"])
        self.kristy.minigames[chat][name_user_lobby]['answer'] = None
        self.kristy.minigames[chat][name_user_lobby]["players"][sender]["correct"] += 1

        if self.kristy.minigames[chat][name_user_lobby]['round'] == self.kristy.minigames[chat][name_user_lobby]['max_rounds']:

            response = "Игра завершилась. Вот таблица результатов: \n" \
                       "• {0}".format(' \n• '.join(['{0} ({1})'.format(player["name"],
                                                                       player["correct"]) for player in sorted(list(self.kristy.minigames[chat][name_user_lobby]["players"].values()),
                                                                                                               key=lambda player: player["correct"],
                                                                                                               reverse=True)]))
            self.kristy.send(peer, response)
            self.kristy.minigames[chat].pop(name_user_lobby)
            if name_user_lobby in self.kristy.lobby[chat]:
                self.kristy.lobby[chat][name_user_lobby]["status"] = "waiting_start"
        else:
            response += "Игра продолжается. {0} через 5 секунды.".format(self.MINIGAMES[name_game]['next'])
            self.kristy.minigames[chat][name_user_lobby]['round'] += 1
            self.kristy.send(peer, response)
            time_now = time.time() + 5
            answer, response, attachments = self.MINIGAMES[name_game]['get'](chat, peer)
            time.sleep(time_now - time.time())

            if not answer:
                self.kristy.send(peer, "Ой-ой, похоже ответа нет")
                # TODO подумать над этим
                return

            self.kristy.minigames[chat][name_user_lobby]['answer'] = answer
            self.kristy.send(peer, response, attachments)



    def get_photo(self, chat, peer):
        users = self.kristy.db.get_users(chat)
        users = [user for user in users if user > 0]
        os.urandom(1)[0] % len(users)
        users_vk = self.kristy.vk.users.get(user_ids=users, fields=["photo_id", "photo_max_orig", "has_photo"]).copy()
        while users_vk:
            random_user = users_vk[os.urandom(1)[0] % len(users)]
            if not random_user["has_photo"]:
                users_vk.remove(random_user)
                continue
            if not random_user["is_closed"] and "photo_id" in random_user:
                photo = "photo" + random_user["photo_id"]
            else:
                photo = self.kristy.get_list_attachments([{"type": "photo", "photo": {"sizes": [{"width": 400, "url": random_user["photo_max_orig"]}]}}], peer)[0]
            return random_user["first_name"], "Кто же на этой фотографии?", photo
        return None, None, None

    def get_status(self, chat, peer):
        users = self.kristy.db.get_users(chat)
        users = users[:1000] if len(users) > 1000 else users
        users_vk = self.kristy.vk.users.get(user_ids=users, fields=["status"]).copy()
        for i in range(len(users_vk)):
            random_users = users_vk[int.from_bytes(os.urandom(2), byteorder='little') % len(users_vk)]
            users_vk.remove(random_users)
            if random_users["status"]:
                return random_users["first_name"], "Чей же это статус? \n" + str(random_users["status"]), []
        return None, None, None
