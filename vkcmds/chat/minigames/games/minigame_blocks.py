import json
import os
import pprint
import random
import time
from enum import Enum, auto
from typing import List, Dict, Union
from copy import deepcopy
import requests
from PIL import Image, ImageDraw, ImageFont

from minigames_manager import Minigame

SIZE_HEIGHT_POLE = 22
SIZE_WIDTH_POLE = 10
BLOCKS_START_COUNT = 24  # 24
POINTS_PER_CUBE = 50


class Probability:
    """
    Вероятности https://dota2.fandom.com/wiki/Random_distribution
    """

    CHANCE5 = 0.003802
    CHANCE10 = 0.014746
    CHANCE15 = 0.032221
    CHANCE20 = 0.055704
    CHANCE25 = 0.084744
    CHANCE30 = 0.118949
    CHANCE40 = 0.201547
    CHANCE45 = 0.249307
    CHANCE50 = 0.302103
    CHANCE70 = 0.571429


HEIGHT_CUBE_PROBABILITY = [[2, Probability.CHANCE70],  # 2 - 70%
                           [3, Probability.CHANCE30]]  # 3 - 30%

WIDTH_CUBE_PROBABILITY = [[1, Probability.CHANCE50],  # 1 - 40%
                          [2, Probability.CHANCE40],  # 2 - 40%
                          [3, Probability.CHANCE5],  # 3 - 15%
                          [4, Probability.CHANCE5]]  # 4 - 5%

COUNT_CUBES_PROBABILITY = [[2, Probability.CHANCE25],  # 2 - 25%
                           [3, Probability.CHANCE50],  # 3 - 50%
                           [4, Probability.CHANCE25]]  # 4 - 25%


class Color(Enum):
    """
    Цвета кубика
    """

    PURPLE = (139, 0, 255)
    RED = (213, 62, 7)
    GREEN = (204, 255, 0)
    BLUE = (0, 191, 255)


class StatusCube(Enum):
    """
    Статус кубика

    NEW     - новый, только что созданный кубик
    CLASSIC - уже существующий кубик, без изменений
    DELETED - только что удалённый кубик, но ещё нужен для отображения
    """

    NEW = auto()
    CLASSIC = auto()
    DELETED = auto()


class Cube:
    """
    Кубик
    """

    def __init__(self, x: int, y: int,
                 color: Color, width: int, height: int,
                 word: str = "", status: StatusCube = StatusCube.NEW):
        """
        :param x: Координата x левого нижнего угла
        :param y: Координата y левого нижнего угла
        :param color: Массив цветов (фиолетовый, красный, салатовый, голубой, белый)
        :param width: Ширина кубика
        :param height: Высота кубика
        :param word: Текст на кубике (может отсутствовать)
        :param status: Отвечает за статус кубика
        """

        self.x = x
        self.y = y
        self.color = color
        self.width = width
        self.height = height
        self.word = word
        self.status = status


def my_print(pole):  # Для отладки неплох
    for x in range(len(pole)):
        for y in range(len(pole[x])):
            print(f"{pole[x][y]}".ljust(4, " ") if pole[x][y] is not None else pole[x][y], end=" ")
        print()


def get_words() -> List[List[Union[str, int]]]:
    """
    Получаем все слова, с их сложностью

    :return: Массив слов со сложностью
    """

    HEADERS = {
        'Content-Type': 'word/plain;charset=UTF-8',
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
        'Content-Type': 'word/plain;charset=UTF-8',
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 11_4) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1.1 Safari/605.1.15'
    }
    URL_RANK = "https://research.google.com/semantris/rank"
    DATA_RANK = ["curated23", None, None, None, [], None, None, "b", 2]  # параметры: [1] - слово
    #            [3] - слова, с которыми сравниваем

    DATA_RANK[1] = word
    DATA_RANK[3] = [cube.word for cube in cubes_data.values() if word.lower() not in cube.word.lower() and cube.word.lower() not in word.lower()]
    data = json.dumps(DATA_RANK).encode('utf8')
    s = requests.Session()
    response = s.post(url=URL_RANK, data=data, headers=HEADERS)
    word_find = response.json()[0][0][0]
    for cube_id, cube in cubes_data.items():
        if cube.word == word_find:
            return cube_id


def probability_selection(probability: List[List], probability_standard: List[List]) -> int:
    """
    Выбирает случайное событие и возвращает значение, при этом изменяя вероятности

    :param probability: Список со значениями и их вероятностями
    :param probability_standard: Список со значениями и их начальной вероятностью

    :return: Значение, которое выпало
    """
    random_number = random.SystemRandom().uniform(0.000001, sum([prob[1] for prob in probability]))
    value_return = -1
    for i in range(len(probability)):
        if 0 < random_number <= probability[i][1]:
            value_return = probability[i][0]
            random_number -= probability[i][1]
            probability[i][1] = 0
        else:
            random_number -= probability[i][1]
        probability[i][1] += probability_standard[i][1]

    return value_return


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


def generate_height_cube(probability) -> int:  # FIXME подумать, надо ли это нам
    """
    Генерирует высоту куба

    :param probability: Список со значениями и их вероятностями

    :return: Значение высоты
    """

    return probability_selection(probability, HEIGHT_CUBE_PROBABILITY)


def generate_width_cube(cubes_data: Dict[int, Cube], words: List[List[Union[str, int]]],
                        score: int, probability: List[List[Union[int, float]]]) -> int:
    """
    Генерирует ширину куба

    :param cubes_data: Словарь всех кубиков {id: {data}}
    :param words: Список слов [слово, сложность]
    :param score: Текущее количество очков
    :param probability:  Список со значениями и их вероятностями

    :return: Значение ширины и список слов, из которого выбирать
    """

    words_pole = [cube.word for cube in cubes_data.values()]
    difficult = get_current_difficulty(score)
    words_suit = {}
    for word in words:
        if word[1] <= difficult and word[0] not in words_pole:
            width = get_amount_columns_word(word[0])
            if width not in words_suit:
                words_suit[width] = []
            words_suit[width].append(word[0])
    for index in range(len(probability)):
        if probability[index][0] not in words_suit:
            probability[index][1] = 0

    width_cube = probability_selection(probability, WIDTH_CUBE_PROBABILITY)

    return width_cube, words_suit[width_cube]


def generate_count_cubes(probability) -> int:  # FIXME подумать, надо ли это нам
    """
    Генерируем количество блоков

    :param probability: Список со значениями и их вероятностями

    :return: Возвращает количество кубиков
    """

    return probability_selection(probability, COUNT_CUBES_PROBABILITY)


def generate_word(words: List[str]) -> str:
    """
    Выбор нового слова

    :param words: Список уже подходящих слов

    :return: Слово
    """

    return random.SystemRandom().choice(words)


def get_current_difficulty(score: int) -> int:
    """
    Возвращает текущую сложность

    :param score: Текущее количество очков

    :return: Сложность
    """

    DIVIDER = 1000

    return score // DIVIDER + 1


def get_amount_columns_word(word: str) -> int:
    """
    Возвращает количство столбцов, которое занимает слово

    :param word: Слово
    :return: количество столбцов, сколько занимает слово
    """
    return 1 if len(word) <= 4 else 2 if len(word) <= 10 else 3 if len(word) <= 17 else 4


def remove_none_blocks(pole: List[list]):
    """
    Удаляет все пустые ячейки, который находятся выше самых верхних блоков.

    :param pole: Поле с id кубиков
    """
    for i in range(SIZE_WIDTH_POLE):
        while pole[i] and pole[i][-1] is None:
            pole[i].pop()


def add_none_blocks(pole: List[list], index: int, height: int):
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
                      text=cube.word, fill=(255, 255, 255), anchor="mm", font=font, stroke_width=2, stroke_fill=(0, 0, 0))
        im.save(f"../tmp/{chat}.png")


def check_similar_cubes(pole: List[List[int]], cubes_data: Dict[int, Cube], cube: Cube) -> bool:
    """
    Проверяет рядом стоящие блоки и меняет текущий блок в зависимости от рядом стоящих

    :param pole: Поле с id кубиков
    :param cubes_data: Словарь всех кубиков {id: Cube}
    :param cube: Текущий кубик

    :return: Возвращает True, если рядом нету похожих блокох, иначе False
    """
    for i in range(cube.height):
        if cube.x - 1 >= 0 and len(pole[cube.x - 1]) > cube.y + i \
                and pole[cube.x - 1][cube.y + i] is not None \
                and cube.color == cubes_data[pole[cube.x - 1][cube.y + i]].color:
            return False

        if cube.x + cube.width < SIZE_WIDTH_POLE and len(pole[cube.x + cube.width]) > cube.y + i \
                and pole[cube.x + cube.width][cube.y + i] is not None \
                and cube.color == cubes_data[pole[cube.x + cube.width][cube.y + i]].color:
            return False

    for i in range(cube.width):
        if cube.y - 1 >= 0 \
                and pole[cube.x + i][cube.y - 1] is not None \
                and cube.color == cubes_data[pole[cube.x + i][cube.y - 1]].color:
            return False

    return True


def spawn_blocks(pole: List[list], cubes_data: Dict[int, Cube], game_data: dict, new_game: bool = True):
    """
    Генерация кубиков

    :param pole: Поле с id кубиков
    :param cubes_data: Словарь всех кубиков {id: Cube}
    :param game_data: Словарь с данными об игре (факторы рандома, счёт и многое)
    :param new_game: True - начальная генерация, False - продолжение игры.
    """
    FACTOR = 2 if new_game else 4
    NUMBER = 1000
    relief_general = [NUMBER for _ in range(SIZE_WIDTH_POLE)]

    blocks_count = BLOCKS_START_COUNT if new_game else generate_count_cubes(game_data["count_cubes_probability"])
    WORDS = get_words()

    for _ in range(blocks_count):
        width_cube, correct_words = generate_width_cube(cubes_data, WORDS, game_data["score"], game_data["width_cube_probability"])

        # ТЕСТИРУЕМ TODO сделать нормально продумано (пожалуйста)
        relief_timed = []
        for i in range(SIZE_WIDTH_POLE - width_cube + 1):
            relief_now = min(relief_general[i: i + width_cube]) * width_cube
            for j in range(width_cube):
                if new_game and min(relief_general[i: i + width_cube]) < relief_general[i + j]:
                    relief_now /= (relief_general[i + j] // min(relief_general[i: i + width_cube]))
            relief_timed.append(relief_now)

        # relief_timed = [sum(relief_general[i: i + width_cube]) - (max(relief_general[i: i + width_cube]) - min(relief_general[i: i + width_cube]))
        #                 for i in range(SIZE_WIDTH_POLE - width_cube + 1)]

        num = random.SystemRandom().uniform(1, sum(relief_timed))
        for i in range(SIZE_WIDTH_POLE - width_cube + 1):
            if num > relief_timed[i]:
                num -= relief_timed[i]
                continue

            height_cube = generate_height_cube(game_data["height_cube_probability"])

            number_min = min(relief_general[i: i + width_cube])
            divider = FACTOR ** height_cube
            for j in range(width_cube):
                relief_general[i + j] = number_min / divider

            cobe_y = max([len(k) for k in pole[i: i + width_cube]])
            for j in range(width_cube):
                add_none_blocks(pole, i + j, cobe_y)

            color_cube = generate_color_cube(new_game)  # FIXME

            cube = Cube(i, cobe_y, color_cube, width_cube, height_cube)
            if check_similar_cubes(pole, cubes_data, cube):
                cube.word = generate_word(correct_words)

            number_cube = max(cubes_data.keys()) + 1 if cubes_data.keys() else 1
            cubes_data.update({number_cube: cube})

            for j in range(width_cube):
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
                          rules='Вам будет показано поле с кубиками со словами (на англ.). '
                                'Игроки по очереди должны написать слово, которое можно ассоциировать со словом на поле. '
                                'Кубики рядом стоящие одинакого цвета будут убраны, и появятся новые кубики. '
                                'Победителя нет, задача команды набрать больше всех очков!',
                          usage='!игра кубики')

    def select_game(self, chat, peer, sender, args):
        self.kristy.lobby[chat]['minigame'] = {
            "name": self.label
        }
        self.kristy.lobby[chat]["time_active"] = time.time() // 60
        self.kristy.send(peer, f"Успешно изменила мини-игру в лобби: \n"  # TODO вынести в отдельный штуку (потому что это одинаково для всех игр)
                               f"• Название: {self.label.upper()} \n"
                               f"• Описание: {self.rules}")
        self.kristy.lobby[chat]['status'] = 'waiting_start'

    def start_game(self, chat, peer, sender):
        all_players_vk = self.kristy.vk.users.get(user_ids=self.kristy.lobby[chat]["players"])
        players = {}
        for player in all_players_vk:
            players.update({player["id"]: {
                "name": f'{player["first_name"]} {player["last_name"]}'
            }})

        self.kristy.send(peer, "Новая мини-игра: \n"  # FIXME пофиксить, чтобы использовать f, а не format
                               "• Название: {0} \n"
                               "• Игроки: \n"
                               "• • {1} \n"
                               "Начало через 10 секунд, приготовьтесь!".format(self.label.upper(),
                                                                               ' \n• • '.join([player["name"] for player in players.values()])))
        time_start = time.time() + 10
        #############################
        pole = [[] for _ in range(SIZE_WIDTH_POLE)]
        cubes_data: Dict[int, Cube] = {}
        game_data: Dict = deepcopy({
            "score": 0,
            "height_cube_probability": HEIGHT_CUBE_PROBABILITY,
            "width_cube_probability": WIDTH_CUBE_PROBABILITY,
            "count_cubes_probability": COUNT_CUBES_PROBABILITY
        })
        spawn_blocks(pole, cubes_data, game_data)

        timed_players = players.copy()
        sequence = []
        for _ in players:
            random_player = random.SystemRandom().choice(list(timed_players.keys()))
            sequence.append(random_player)
            timed_players.pop(random_player)

        draw_pole(chat, cubes_data)
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
                'game_data': game_data
            }
        })
        self.kristy.send(peer, f'Игра началась. '
                               f'Порядок: {", ".join([players[player]["name"] for player in sequence])}. \n'
                               f'Первым ходит: {players[sequence[0]]["name"]}.',
                         pole_image)

    def check_game(self, chat, peer, sender, msg: str):
        if self.kristy.minigames[chat]["sequence"][0] != sender or not msg or not msg.startswith('.'):
            return
        msg = msg[1:]

        pole: List[List[int]] = self.kristy.minigames[chat]["pole"]
        cubes_data: Dict[int, Cube] = self.kristy.minigames[chat]["cubes_data"]
        game_data: Dict = self.kristy.minigames[chat]["game_data"]

        cube_find_id = get_rank_word(msg, cubes_data)
        cube_find_word = cubes_data[cube_find_id].word
        delete_cubes_ids = remove_cubes_similar_color(pole, cubes_data, cubes_data[cube_find_id].x, cubes_data[cube_find_id].y)
        for cube_id in delete_cubes_ids:
            game_data["score"] += POINTS_PER_CUBE
            cubes_data[cube_id].status = StatusCube.DELETED
        move_down_blocks(pole, cubes_data)
        remove_none_blocks(pole)

        spawn_blocks(pole, cubes_data, game_data, False)
        draw_pole(chat, cubes_data)

        self.kristy.minigames[chat]["sequence"] = self.kristy.minigames[chat]["sequence"][1:] + self.kristy.minigames[chat]["sequence"][0:1]
        uploads = self.kristy.vk_upload.photo_messages(photos=f"../tmp/{chat}.png")[0]
        pole_image = f'photo{uploads["owner_id"]}_{uploads["id"]}'
        os.remove(f"../tmp/{chat}.png")
        self.kristy.lobby[chat]['time_active'] = time.time() // 60

        status_end_game = False
        for i in range(SIZE_WIDTH_POLE):
            if SIZE_HEIGHT_POLE < len(pole[i]):
                status_end_game = True
                break
        if status_end_game:
            self.kristy.send(peer, f'Нашла сходство со словом: {cube_find_word} \n'
                                   f'Вы проиграли! Вас счёт: {game_data["score"]}', pole_image)
            self.kristy.minigames.update({chat: {}})
            self.kristy.lobby[chat]["status"] = "waiting_start"
        else:
            self.kristy.send(peer, f'Нашла сходство со словом: {cube_find_word} \n'
                                   f'Счёт: {game_data["score"]} \n'
                                   f'Следующий ходит: {self.kristy.minigames[chat]["players"][self.kristy.minigames[chat]["sequence"][0]]["name"]}',
                             pole_image)
