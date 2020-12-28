from minigames_manager import Minigame
import time
import os
import requests
import re
from PIL import Image, ImageDraw
from enum import Enum, auto

MIN_SIZE = 4
MAX_SIZE = 8


class Column(Enum):
    a = auto()
    b = auto()
    c = auto()
    d = auto()
    e = auto()
    f = auto()
    g = auto()
    h = auto()


class Photo(Minigame):
    def __init__(self, kristy):
        Minigame.__init__(self, kristy,
                          label='стрельба',
                          rules="Каждый участник по очереди стреляет в поле (размер от {0} до {1}). В этих ячейках спрятались вы. "
                                "Задача: выжить и застрелить других игроков.".format(MIN_SIZE, MAX_SIZE),
                          usage='!игра стрельба <размер поля от {0} до {1}'.format(MIN_SIZE, MAX_SIZE),
                          min_args=1)

    def select_game(self, chat, peer, sender, args):
        self.kristy.lobby[chat]['status'] = 'waiting_start'
        if not args[1].isdigit() or (args[1].isdigit() and not MIN_SIZE <= int(args[1]) <= MAX_SIZE):
            self.kristy.send(peer, 'Неверный формат размера поля (от {0} до {1})'.format(MIN_SIZE, MAX_SIZE))
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
        if len(self.kristy.lobby[chat]["players"]) < 2:
            self.kristy.send(peer, "Недостаточно игроков. Минимум 2")
            return
        size_map = self.kristy.lobby[chat]['minigame']["size_map"]
        if size_map * size_map < len(self.kristy.lobby[chat]["players"]):
            self.kristy.send(peer, "Слишком много игроков")
            return
        self.kristy.lobby[chat]['status'] = 'game_playing'
        all_players_vk = self.kristy.vk.users.get(user_ids=self.kristy.lobby[chat]["players"], fields=["photo_100"])
        players = {}
        for player in all_players_vk:
            players.update({player["id"]: {
                "name": player["first_name"] + " " + player["last_name"],
                "photo": player["photo_100"]
            }})

        self.kristy.send(peer, "Новая мини-игра: \n"
                               "• Название: {0} \n"
                               "• Размер: {1} \n"
                               "• Игроки: \n"
                               "• • {2} \n"
                               "Начало через 10 секунд, приготовьтесь!".format(self.label.upper(),
                                                                               size_map,
                                                                               ' \n• • '.join([player["name"] for player in players.values()])))
        time_start = time.time() + 10
        players_photos = {}
        for player in players:
            img_data = requests.get(players[player]["photo"]).content
            time_now = time.time()
            if not os.path.isdir("../tmp"):
                os.makedirs("../tmp")
            with open('../tmp/image_timed{0}.jpg'.format(time_now), 'wb') as handler:
                handler.write(img_data)
            players[player]["photo"] = '../tmp/image_timed{0}.jpg'.format(time_now)
            players_photos.update({player: players[player]["photo"]})
        pole = [[{None: "unshoted"}] * size_map for i in range(size_map)]
        for number, player in enumerate(players):
            random_cell = os.urandom(1)[0] % (size_map * size_map)
            while pole[random_cell // size_map][random_cell % size_map] != {None: "unshoted"}:
                random_cell = os.urandom(1)[0] % (size_map * size_map)
            pole[random_cell // size_map][random_cell % size_map] = {player: "unshoted"}
        timed_players = players.copy()
        sequence = []
        for player in players:
            random_player = list(timed_players.keys())[os.urandom(1)[0] % len(list(timed_players.keys()))]
            sequence.append(random_player)
            timed_players.pop(random_player)

        uploads = self.kristy.vk_upload.photo_messages(photos='./minigame_images/pole{0}.jpg'.format(size_map))[0]
        pole_image = 'photo{0}_{1}'.format(uploads["owner_id"], uploads["id"])
        time.sleep(time_start - time.time())
        self.kristy.lobby[chat]['time_active'] = time.time() // 60

        self.kristy.minigames.update({
            chat: {
                'name': self.label,
                'players': players,
                'sequence': sequence,
                'pole': pole

            }
        })
        self.kristy.send(peer, "Игра началась. Первым стреляет: {0}".format(players[sequence[0]]["name"]), pole_image)

    def check_game(self, chat, peer, sender, msg):
        msg = msg.lower()
        if self.kristy.minigames[chat]["sequence"][0] != sender:
            return
        if not re.findall(r"^([a-h])([12345678])$", msg.strip()):
            return
        size_map = self.kristy.lobby[chat]['minigame']["size_map"]
        shot_y, shot_x = re.findall(r"^([a-h])([12345678])$", msg.strip())[0]
        shot_x = int(shot_x) - 1
        shot_y = Column[shot_y].value - 1
        if shot_x + 1 >= size_map and shot_y + 1 >= size_map:
            return
        person, status = list(self.kristy.minigames[chat]["pole"][shot_y][shot_x].items())[0]
        if status == "shoted":
            self.kristy.send(peer, "В эту ячейку уже стреляли. Выберите другую")
            return
        if person:
            if person == sender:
                response = "{0} попадает в себя. Жалко( \n".format(self.kristy.minigames[chat]["players"][sender]["name"])
                self.kristy.minigames[chat]["sequence"].remove(person)
            else:
                response = "{0} попадает в цель. {1} погибает. \n".format(self.kristy.minigames[chat]["players"][sender]["name"],
                                                                          self.kristy.minigames[chat]["players"][person]["name"])
                self.kristy.minigames[chat]["sequence"].remove(person)
                self.kristy.minigames[chat]["sequence"] = self.kristy.minigames[chat]["sequence"][1:] + self.kristy.minigames[chat]["sequence"][0:1]
        else:
            response = "{0} делает промах. \n".format(self.kristy.minigames[chat]["players"][sender]["name"])
            self.kristy.minigames[chat]["sequence"] = self.kristy.minigames[chat]["sequence"][1:] + self.kristy.minigames[chat]["sequence"][0:1]
        self.kristy.minigames[chat]["pole"][shot_y][shot_x] = {person: "shoted"}
        with Image.open("./minigame_images/pole{0}.jpg".format(size_map)) as im:
            draw = ImageDraw.Draw(im)
            for y in range(size_map):
                for x in range(size_map):
                    person, status = list(self.kristy.minigames[chat]["pole"][y][x].items())[0]
                    if status == "shoted":
                        if person:
                            img = Image.open(self.kristy.minigames[chat]["players"][person]["photo"])
                            im.paste(img, (82 + 105 * x, 82 + 105 * y))
                        draw.line((92 + 105 * x, 92 + 105 * y, 172 + 105 * x, 172 + 105 * y), fill=(255, 0, 0), width=4)
                        draw.line((92 + 105 * x, 172 + 105 * y, 172 + 105 * x, 92 + 105 * y), fill=(255, 0, 0), width=4)
            im.save("../tmp/{0}.jpg".format(chat))
        uploads = self.kristy.vk_upload.photo_messages(photos="../tmp/{0}.jpg".format(chat))[0]
        pole_image = 'photo{0}_{1}'.format(uploads["owner_id"], uploads["id"])
        os.remove("../tmp/{0}.jpg".format(chat))
        if len(self.kristy.minigames[chat]["sequence"]) < 2:
            response += "\n {0} побеждает в этой стрельбе. Мои поздравления!".format(self.kristy.minigames[chat]["players"][self.kristy.minigames[chat]["sequence"][0]]["name"])
            self.kristy.minigames.update({chat: {}})
            self.kristy.lobby[chat]["status"] = "waiting_start"
            self.kristy.send(peer, response, pole_image)
            return
        response += "Следущий делает выстрел: {0}".format(self.kristy.minigames[chat]["players"][self.kristy.minigames[chat]["sequence"][0]]["name"])
        self.kristy.send(peer, response, pole_image)
