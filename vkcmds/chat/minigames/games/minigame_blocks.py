import json
import os
import random
import time
from enum import Enum
from typing import List, Dict

import requests
from PIL import Image, ImageDraw, ImageFont

from minigames_manager import Minigame

SIZE_HEIGHT_POLE = 22
SIZE_WIDTH_POLE = 10
BLOCKS_START_COUNT = 24
POINTS_PER_CUBE = 50


class Color(Enum):
    PURPLE = (139, 0, 255)
    RED = (213, 62, 7)
    GREEN = (204, 255, 0)
    BLUE = (0, 191, 255)


class Cube:
    """
    Кубик

    """

    def __init__(self, x, y, color, width, height, text=""):
        """

        :param x: Координата x левого нижнего угла
        :param y: Координата y левого нижнего угла
        :param color: Массив цветов (фиолетовый, красный, салатовый, голубой, белый)
        :param width: Ширина кубика
        :param height: Высота кубика
        :param text: Текст на кубике (может отсутствовать)
        """
        self.x = x
        self.y = y
        self.color = color
        self.width = width
        self.height = height
        self.text = text


def my_print(pole): # Для отладки неплох
    for x in range(len(pole)):
        for y in range(len(pole[x])):
            print(f"{pole[x][y]}".ljust(4, " ") if pole[x][y] is not None else pole[x][y], end=" ")
        print()


def get_words() -> List[list]:
    """
    Получаем все слова, с их сложностью
    :return: Массив слов со сложностью
    """
    HEADERS = {
        'Content-Type': 'text/plain;charset=UTF-8',
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 11_4) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1.1 Safari/605.1.15'
    }
    URL_START = "https://research.google.com/semantris/start"
    DATA_START = [None, None, None, "curated23", 1, "b"]

    data = json.dumps(DATA_START).encode('utf8')
    s = requests.Session()
    response = s.post(url=URL_START, data=data, headers=HEADERS)
    return response.json()[5]


def get_rank_word(word: str, cubes_data: Dict[int, Cube]) -> int:
    """
    Сраниваем слово с другими словами на поле

    :param word: Слово
    :param cubes_data: Словарь всех кубиков {id: {data}}
    :return: Id самого похожего слова в cubes_data
    """
    HEADERS = {
        'Content-Type': 'text/plain;charset=UTF-8',
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 11_4) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1.1 Safari/605.1.15'
    }
    URL_RANK = "https://research.google.com/semantris/rank"
    DATA_RANK = ["curated23", None, None, None, [], None, None, "b", 2]  # параметры: [1] - слово
    #            [3] - слова, с которыми сравниваем

    DATA_RANK[1] = word
    DATA_RANK[3] = [cube.text for cube in cubes_data.values() if word.lower() not in cube.text.lower() and cube.text.lower() not in word.lower()]
    data = json.dumps(DATA_RANK).encode('utf8')
    s = requests.Session()
    response = s.post(url=URL_RANK, data=data, headers=HEADERS)
    word_find = response.json()[0][0][0]
    for cube_id, cube in cubes_data.items():
        if cube.text == word_find:
            return cube_id


def choose_word(cube_data: dict, words: list, score: int) -> str:  # TODO сделать нормально типы
    """
    Выбор нового слова

    :param cube_data: Словарь всех кубиков {id: {data}}
    :param words: Список слов [слово, сложность]
    :param score: Текущее количество очков
    """
    # TODO сделать как-то, чтобы можно было сгенерировать без слова
    words_list = list(filter(lambda x: x[1] <= score // 1000 + 1, words))
    while True:
        word, number = random.SystemRandom().choice(words_list)
        for cube in cube_data.values():
            if cube.text == word:
                break
        else:
            return word


def generate_color_cube(new_game: bool) -> List[List[int]]:
    """
    Генерирует цвет (иногда несколько) кубу
    :param new_game: True - начальная генерация, False - продолжение игры.
    :return: Возвращает список цветов [r, g, b]
    """
    # TODO Сделать несколько цветов
    WHITE = (255, 255, 255)
    # return [random.SystemRandom().choice(COLORS)]
    return random.SystemRandom().choice([e for e in Color])


def generate_height_cube() -> int:
    """
    Генерирует высоту куба (пока 50 на 50)
    :return: значение высоты (2-3)
    """
    return random.SystemRandom().randint(2, 3)


def get_amount_columns_word(word) -> int:
    """
    Возвращает количство столбцов, которое занимает слово

    :param word: Слово
    :return: количество столбцов, сколько занимает слово
    """
    if len(word) <= 4:
        return 1
    elif len(word) <= 10:
        return 2
    elif len(word) <= 17:
        return 3
    else:
        return 4


def remove_none_blocks(pole):
    """
    Удаляет все пустые ячейки, который находятся выше самых верхних блоков.

    :param pole: Поле с id кубиков
    """
    for i in range(SIZE_WIDTH_POLE):
        while pole[i] and pole[i][-1] is None:
            pole[i].pop()


def add_none_blocks(pole: List[list], index, height):
    """
    Добавляет пустые блоки в выбранную колонку до выбранной высоты

    :param pole: Поле с id кубиков
    :param index: Номер столба
    :param height: высота, до которой нужно дойти (не включая)
    """
    for i in range(len(pole[index]), height):
        pole[index].append(None)


def draw_pole(chat: int, cubes_data: Dict[int, Cube]):
    """
    Создаёт картинку с полем

    :param chat: Id чата
    :param cubes_data: Словарь всех кубиков {id: Cube}
    """

    with Image.open("./minigame_images/pole_blocks.png") as im:
        draw = ImageDraw.Draw(im)
        for cube in cubes_data.values():
            color_outfill = tuple([int(number * 0.8) for number in cube.color.value])
            draw.rounded_rectangle((6 + cube.x * 92, 807 - (cube.y + cube.height) * 31, 6 + (cube.x + cube.width) * 92 - 1, 807 - cube.y * 31 - 1),
                                   fill=cube.color.value, outline=color_outfill, radius=12, width=2)
            font = ImageFont.truetype("fonts/20219.ttf", 32)
            draw.text((6 + cube.x * 92 + cube.width * 46, 807 - (cube.y + cube.height) * 31 + cube.height * 15.5),
                      text=cube.text, fill=(255, 255, 255), anchor="mm", font=font, stroke_width=1, stroke_fill=(0, 0, 0))
        im.save(f"../tmp/{chat}.png")


def spawn_blocks(pole: List[list], cubes_data: dict, new_game: bool = True, score: int = 0):
    """
    Генерация кубиков

    :param pole: Поле с id кубиков
    :param cubes_data: Словарь всех кубиков {id: Cube}
    :param new_game: True - начальная генерация, False - продолжение игры.
    :param score: Текущее количество очков
    """
    FACTOR = 2
    NUMBER = 1000
    relief_general = [NUMBER for _ in range(SIZE_WIDTH_POLE)]
    blocks_count = BLOCKS_START_COUNT if new_game else random.SystemRandom().randint(2, 4)
    WORDS = get_words()
    for _ in range(blocks_count):
        word = choose_word(cubes_data, WORDS, score)
        count_columns = get_amount_columns_word(word)

        # ТЕСТИРУЕМ
        # relief_timed = [sum(relief_general[i: i + count_columns]) for i in range(SIZE_WIDTH_POLE - count_columns + 1)]
        relief_timed = [sum(relief_general[i: i + count_columns]) - (max(relief_general[i: i + count_columns]) - min(relief_general[i: i + count_columns]))
                        for i in range(SIZE_WIDTH_POLE - count_columns + 1)]

        num = random.SystemRandom().uniform(1, sum(relief_timed))
        for i in range(SIZE_WIDTH_POLE - count_columns + 1):
            if num > relief_timed[i]:
                num -= relief_timed[i]
                continue

            height_cube = generate_height_cube()

            number_min = min(relief_general[i: i + count_columns])
            divider = FACTOR ** height_cube
            for j in range(count_columns):
                relief_general[i + j] = number_min / divider

            cobe_y = max([len(k) for k in pole[i: i + count_columns]])
            for j in range(count_columns):
                add_none_blocks(pole, i + j, cobe_y)

            color_cube = generate_color_cube(new_game)

            cube = Cube(i, cobe_y, color_cube, count_columns, height_cube, word)
            number_cube = max(cubes_data.keys()) + 1 if cubes_data.keys() else 1
            cubes_data.update({number_cube: cube})

            for j in range(count_columns):
                for _ in range(height_cube):
                    pole[i + j].append(number_cube)

            if max(relief_general) < NUMBER:
                multiplier = NUMBER / max(relief_general)
                relief_general = list(map(lambda x: x * multiplier, relief_general))
            break


def remove_cubes_similar_color(pole: List[List[int]], cubes_data: Dict[int, Cube], x_now: int, y_now: int) -> List[int]:
    cube_id_now = pole[x_now][y_now]
    mas = [cube_id_now]
    pole[x_now][y_now] = None
    cube_now = cubes_data[cube_id_now]
    # Вверх
    if y_now + 1 < len(pole[x_now]) \
            and pole[x_now][y_now + 1] is not None \
            and cubes_data[pole[x_now][y_now + 1]].color == cube_now.color:
        mas += remove_cubes_similar_color(pole, cubes_data, x_now, y_now + 1)
    # Вниз
    if y_now - 1 >= 0 \
            and pole[x_now][y_now - 1] is not None \
            and cubes_data[pole[x_now][y_now - 1]].color == cube_now.color:
        mas += remove_cubes_similar_color(pole, cubes_data, x_now, y_now - 1)
    # Вправо
    if x_now + 1 < len(pole) and len(pole[x_now + 1]) > y_now \
            and pole[x_now + 1][y_now] is not None \
            and cubes_data[pole[x_now + 1][y_now]].color == cube_now.color:
        mas += remove_cubes_similar_color(pole, cubes_data, x_now + 1, y_now)
    # Влево
    if x_now - 1 >= 0 and len(pole[x_now - 1]) > y_now \
            and pole[x_now - 1][y_now] is not None \
            and cubes_data[pole[x_now - 1][y_now]].color == cube_now.color:
        mas += remove_cubes_similar_color(pole, cubes_data, x_now - 1, y_now)

    return list(set(mas))


def move_down_blocks(pole: List[List[int]], cubes_data: Dict[int, Cube]):
    while True:
        for cube_id, cube in cubes_data.items():
            if cube.y - 1 < 0:
                continue
            for i in range(cube.width):
                if pole[cube.x + i][cube.y - 1] is not None:
                    break
            else:
                for i in range(cube.width):
                    for j in range(cube.height):
                        pole[cube.x + i][cube.y + j - 1], pole[cube.x + i][cube.y + j] = pole[cube.x + i][cube.y + j], pole[cube.x + i][cube.y + j - 1]
                cubes_data[cube_id].y -= 1
                break
        else:
            break


class Cubes(Minigame):
    def __init__(self, kristy):
        Minigame.__init__(self, kristy,
                          label='кубики',
                          rules='Будет показызаны кубики со словами. '
                                'Вам нужно находить ассоциации с этими словами.',
                          usage='!игра кубики')

    def select_game(self, chat, peer, sender, args):
        self.kristy.lobby[chat]['status'] = 'waiting_start'
        self.kristy.lobby[chat]['minigame'] = {
            "name": self.label
        }
        self.kristy.lobby[chat]["time_active"] = time.time() // 60
        self.kristy.send(peer, "Успешно изменила мини-игру в лобби: \n"
                               "• Название: {0} \n"
                               "• Описание: {1}".format(self.label.upper(),
                                                        self.rules))

    def start_game(self, chat, peer, sender):
        all_players_vk = self.kristy.vk.users.get(user_ids=self.kristy.lobby[chat]["players"])
        players = {}
        for player in all_players_vk:
            players.update({player["id"]: {
                "name": player["first_name"] + " " + player["last_name"]
            }})

        self.kristy.send(peer, "Новая мини-игра: \n"
                               "• Название: {0} \n"
                               "• Игроки: \n"
                               "• • {1} \n"
                               "Начало через 10 секунд, приготовьтесь!".format(self.label.upper(),
                                                                               ' \n• • '.join([player["name"] for player in players.values()])))
        time_start = time.time() + 10
        #############################
        pole = [[] for _ in range(SIZE_WIDTH_POLE)]
        cubes_data: Dict[int, Cube] = {}
        spawn_blocks(pole, cubes_data)

        draw_pole(chat, cubes_data)
        timed_players = players.copy()
        sequence = []
        for _ in players:
            random_player = list(timed_players.keys())[os.urandom(1)[0] % len(list(timed_players.keys()))]
            sequence.append(random_player)
            timed_players.pop(random_player)

        uploads = self.kristy.vk_upload.photo_messages(photos=f"../tmp/{chat}.png")[0]
        pole_image = f'photo{uploads["owner_id"]}_{uploads["id"]}'
        os.remove(f"../tmp/{chat}.png")
        #############################
        time.sleep(time_start - time.time())
        self.kristy.lobby[chat]['time_active'] = time.time() // 60
        self.kristy.lobby[chat]['status'] = 'game_playing'
        self.kristy.minigames.update({
            chat: {
                'name': self.label,
                'players': players,
                'sequence': sequence,
                'cubes_data': cubes_data,
                'pole': pole,
                'score': 0

            }
        })
        self.kristy.send(peer, f'Игра началась. '
                               f'Порядок: {", ".join([players[player]["name"] for player in sequence])}. \n'
                               f'Первым ходит: {players[sequence[0]]["name"]}.',
                         pole_image)

    def check_game(self, chat, peer, sender, msg):
        if self.kristy.minigames[chat]["sequence"][0] != sender:
            return
        pole: List[List[int]] = self.kristy.minigames[chat]["pole"]
        cubes_data: Dict[int, Cube] = self.kristy.minigames[chat]["cubes_data"]
        score: int = self.kristy.minigames[chat]["score"]
        cube_find_id = get_rank_word(msg, cubes_data)
        cube_find_word = cubes_data[cube_find_id].text
        delete_cubes_ids = remove_cubes_similar_color(pole, cubes_data, cubes_data[cube_find_id].x, cubes_data[cube_find_id].y)
        for cube_id in delete_cubes_ids:
            score += POINTS_PER_CUBE
            cubes_data.pop(cube_id)
        move_down_blocks(pole, cubes_data)
        remove_none_blocks(pole)
        spawn_blocks(pole, cubes_data, False, score)
        draw_pole(chat, cubes_data)

        self.kristy.minigames[chat]["sequence"] = self.kristy.minigames[chat]["sequence"][1:] + self.kristy.minigames[chat]["sequence"][0:1]
        uploads = self.kristy.vk_upload.photo_messages(photos=f"../tmp/{chat}.png")[0]
        pole_image = f'photo{uploads["owner_id"]}_{uploads["id"]}'
        os.remove(f"../tmp/{chat}.png")
        self.kristy.lobby[chat]['time_active'] = time.time() // 60

        self.kristy.minigames[chat]["pole"] = pole
        self.kristy.minigames[chat]["cubes_data"] = cubes_data
        self.kristy.minigames[chat]["score"] = score
        status_end_game = False
        for i in range(SIZE_WIDTH_POLE):
            if SIZE_HEIGHT_POLE < len(pole[i]):
                status_end_game = True
                break
        if status_end_game:
            self.kristy.send(peer, f'Вы проиграли! Вас счёт: {score}', pole_image)
            self.kristy.minigames.update({chat: {}})
            self.kristy.lobby[chat]["status"] = "waiting_start"
        else:
            self.kristy.send(peer, f'Нашла сходство со словом: {cube_find_word} \n'
                                   f'Счёт: {score} \n'
                                   f'Следующий ходит: {self.kristy.minigames[chat]["players"][self.kristy.minigames[chat]["sequence"][0]]["name"]}',
                             pole_image)
