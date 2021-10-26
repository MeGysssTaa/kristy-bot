from minigames_manager import Minigame
import time
import os
import re
MIN_ROUNDS = 10
MAX_ROUNDS = 60


class Photo(Minigame):
    def __init__(self, kristy):
        Minigame.__init__(self, kristy,
                          label='домен',
                          rules='Вам будет показан короткий адрес участника беседы. '
                                'Вы должны написать имя аккаунта с этим статусом (как в ВК), '
                                'то есть Петя, Пётр и Петр <- это три разных имени. Можно использовать заглавные или строчные буквы.',
                          usage='!игра домен <число раундов от {0} до {1}>'.format(MIN_ROUNDS, MAX_ROUNDS),
                          min_args=1)

    def select_game(self, chat, peer, sender, args):
        if not args[1].isdigit() or (args[1].isdigit() and not MIN_ROUNDS <= int(args[1]) <= MAX_ROUNDS):
            self.kristy.send(peer, 'Неверный формат количества раундов (от {0} до {1})'.format(MIN_ROUNDS, MAX_ROUNDS))
            return
        max_rounds = int(args[1])
        self.kristy.lobby[chat]['status'] = 'waiting_start'
        self.kristy.lobby[chat]['minigame'] = {
            "name": self.label,
            "settings": {
                "rounds_max": max_rounds
            }
        }
        self.kristy.lobby[chat]["time_active"] = time.time() // 60
        self.kristy.send(peer, "Успешно изменила мини-игру в лобби: \n"
                               "• Название: {0} \n"
                               "• Описание: {1} \n"
                               "• Число раундов: {2}".format(self.label.upper(),
                                                             self.rules,
                                                             str(max_rounds)))

    def start_game(self, chat, peer, sender):
        self.kristy.lobby[chat]['status'] = 'game_playing'

        all_players_vk = self.kristy.vk.users.get(user_ids=self.kristy.lobby[chat]["players"])

        players = {}
        max_rounds = self.kristy.lobby[chat]['minigame']["settings"]["rounds_max"]
        for player in all_players_vk:
            players.update({player["id"]: {
                "name": player["first_name"] + " " + player["last_name"],
                "correct": 0
            }})

        self.kristy.send(peer, "Новая мини-игра: \n"
                               "• Название: {0} \n"
                               "• Раундов: {1} \n"
                               "• Игроки: \n"
                               "• • {2} \n"
                               "Начало через 10 секунд, приготовьтесь!".format(self.label.upper(),
                                                                               max_rounds,
                                                                               ' \n• • '.join([player["name"] for player in players.values()])))
        time_now = time.time() + 10
        answer, domain = self.get(chat, peer)
        time.sleep(time_now - time.time())

        self.kristy.lobby[chat]['time_active'] = time.time() // 60
        if not answer:
            self.kristy.send(peer, "Ой-ой, похоже ответа нет")
            self.kristy.lobby[chat]['status'] = 'waiting_start'
            return

        self.kristy.minigames.update({
            chat: {
                'name': self.label,
                'players': players,
                'round': 1,
                'max_rounds': max_rounds,
                'answer': answer

            }
        })

        self.kristy.send(peer, "Игра началась. Чей же это короткий адрес? \n" + domain)

    def check_game(self, chat, peer, sender, msg):
        if msg.strip().lower() != self.kristy.minigames[chat]["answer"].strip().lower():
            return
        self.kristy.lobby[chat]['time_active'] = time.time() // 60
        self.kristy.minigames[chat]['answer'] = None
        self.kristy.minigames[chat]["players"][sender]["correct"] += 1
        response = '{0} отвечает правильно. \n'.format(self.kristy.minigames[chat]["players"][sender]["name"])
        if self.kristy.minigames[chat]['round'] == self.kristy.minigames[chat]['max_rounds']:
            response += "Игра завершилась. Вот таблица результатов: \n"
            for number, player in enumerate(sorted(list(self.kristy.minigames[chat]["players"].values()), key=lambda player: player["correct"], reverse=True)):
                response += "{0}. {1} ({2}) \n".format(number + 1,
                                                       player["name"],
                                                       player["correct"])
            self.kristy.send(peer, response)
            self.kristy.minigames.update({chat: {}})
            self.kristy.lobby[chat]["status"] = "waiting_start"
        else:
            response += "Игра продолжается. Следующий короткий адрес через 5 секунд."
            self.kristy.minigames[chat]['round'] += 1
            self.kristy.send(peer, response)
            time_now = time.time() + 5
            answer, domain = self.get(chat, peer)
            time.sleep(time_now - time.time())

            if not answer:
                self.kristy.send(peer, "Ой-ой, похоже ответа нет")
                # TODO подумать над этим
                return

            self.kristy.minigames[chat]['answer'] = answer
            self.kristy.send(peer, "Чей же это короткий адрес? \n" + domain)

    def get(self, chat, peer):
        users = self.kristy.db.get_users(chat)
        users = users[:1000] if len(users) > 1000 else users
        users_vk = self.kristy.vk.users.get(user_ids=users, fields=["domain"]).copy()
        for i in range(len(users_vk)):
            random_user = users_vk[int.from_bytes(os.urandom(2), byteorder='little') % len(users_vk)]
            users_vk.remove(random_user)
            if not re.findall(r"^id\d+$", random_user["domain"]):
                return random_user["first_name"], random_user["domain"]
        return None, None
