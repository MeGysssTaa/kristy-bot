import os
import pprint
import re
from enum import Enum, auto

from PIL import Image, ImageDraw, ImageFont
import random
import time
from typing import List, Dict

from minigames_manager import Minigame

MIN_SIZE = 4
MAX_SIZE = 8
SIZE_CELL = 130
SIZE_LETTER = 80
SIZE_ANIME = 100


class Column(Enum):
    a = auto()
    b = auto()
    c = auto()
    d = auto()
    e = auto()
    f = auto()
    g = auto()
    h = auto()


class Cell:
    """
    Класс ячейки
    """

    def __init__(self, image_id=None, is_available=True, is_selected=False):
        """
        :param image_id: Id изображения в dict изображений
        :param is_available: Доступен ли данная ячейка для открытия
        :param is_selected: Перевёрнута ли сейчас эта ячейка
        """

        self.image_id = image_id
        self.is_available = is_available
        self.is_selected = is_selected


def prepare_mask(size, antialias=2):
    """
    Маска, чтобы вырезать фото

    :param size: размер (x, y)
    :param antialias: (качество, хз) XD

    :return: Маска
    """
    mask = Image.new('L', (size[0] * antialias, size[1] * antialias), 0)
    ImageDraw.Draw(mask).rounded_rectangle((0, 0) + mask.size, radius=100, fill=255)
    return mask.resize(size, Image.ANTIALIAS)


def draw_pole(pole: List[List[Cell]], images_data: Dict[int, str]):
    """
    Рисует поле и возращает путь до файла

    :param pole: Поле с ячейками
    :param images_data: Дата с картинками {id: путь}

    :return: Путь до картинки
    """

    size_pole = len(pole)
    img = Image.new('RGBA', (size_pole * SIZE_CELL + 2 * SIZE_LETTER + 1,
                             size_pole * SIZE_CELL + 2 * SIZE_LETTER + 1), 'white')
    draw = ImageDraw.Draw(img)

    color_lines = (87, 65, 42)
    color_text = (0, 0, 0)
    color_stroke_fill_text = (0, 0, 0)
    stroke_width_text = 0
    font = ImageFont.truetype("fonts/20219.ttf", 64)
    for i in range(size_pole + 1):
        # вертикальный палочки
        draw.line((SIZE_LETTER + i * SIZE_CELL, SIZE_LETTER,
                   SIZE_LETTER + i * SIZE_CELL, SIZE_LETTER + SIZE_CELL * size_pole),
                  fill=color_lines, width=4)
        # горизонтальные палочки
        draw.line((SIZE_LETTER, SIZE_LETTER + i * SIZE_CELL,
                   SIZE_LETTER + SIZE_CELL * size_pole, SIZE_LETTER + i * SIZE_CELL),
                  fill=color_lines, width=4)

    for i in range(size_pole):
        # вертикальные буквы (слева)
        draw.text((SIZE_LETTER // 2, SIZE_LETTER + SIZE_CELL // 2 + SIZE_CELL * i),
                  text=chr(ord('A') + i), fill=color_text, anchor="mm",
                  font=font, stroke_width=stroke_width_text, stroke_fill=color_stroke_fill_text)
        # горизонтальные цифры (сверху)
        draw.text((SIZE_LETTER + SIZE_CELL // 2 + SIZE_CELL * i, SIZE_LETTER // 2),
                  text=chr(ord('1') + i), fill=color_text, anchor="mm",
                  font=font, stroke_width=stroke_width_text, stroke_fill=color_stroke_fill_text)
        # вертикальные буквы (справа)
        draw.text((SIZE_LETTER * 3 // 2 + SIZE_CELL * size_pole, SIZE_LETTER + SIZE_CELL // 2 + SIZE_CELL * i),
                  text=chr(ord('A') + i), fill=color_text, anchor="mm",
                  font=font, stroke_width=stroke_width_text, stroke_fill=color_stroke_fill_text)
        # горизонтальные цифры (сверху)
        draw.text((SIZE_LETTER + SIZE_CELL // 2 + SIZE_CELL * i, SIZE_LETTER * 3 // 2 + SIZE_CELL * size_pole),
                  text=chr(ord('1') + i), fill=color_text, anchor="mm",
                  font=font, stroke_width=stroke_width_text, stroke_fill=color_stroke_fill_text)

    for i in range(size_pole):
        for j in range(size_pole):

            if pole[i][j].is_available and pole[i][j].is_selected:
                photo = Image.open(f"anime/icons/{images_data[pole[i][j].image_id]}")
            else:
                photo = Image.open(f"anime/icon_close.jpg")
            if pole[i][j].is_available:
                img.paste(photo, (SIZE_LETTER + (SIZE_CELL - SIZE_ANIME) // 2 + SIZE_CELL * j + 1,
                                  SIZE_LETTER + (SIZE_CELL - SIZE_ANIME) // 2 + SIZE_CELL * i + 1),
                          mask=prepare_mask((SIZE_ANIME, SIZE_ANIME), 8))
    save_file = f"../tmp/{str(random.random())}.png"
    img.save(save_file)
    return save_file


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
                          usage=f'!игра ячейки <размер поля от {MIN_SIZE} до {MAX_SIZE}>',
                          min_args=1)

    def select_game(self, chat, peer, sender, args):

        if not args[1].isdigit() or (args[1].isdigit() and (int(args[1]) < MIN_SIZE or int(args[1]) > MAX_SIZE)):
            self.kristy.send(peer, f'Неверный формат размера поля (от {MIN_SIZE} до {MAX_SIZE}).')
            return
        size_map = int(args[1])
        self.kristy.lobby[chat]['minigame'] = {
            "name": self.label,
            "size_map": size_map
        }
        self.kristy.lobby[chat]["time_active"] = time.time() // 60
        self.kristy.send(peer, "Успешно изменила мини-игру в лобби: \n"
                               f"• Название: {self.label.upper()} \n"
                               f"• Описание: {self.rules} \n"
                               f"• Размер: {size_map} \n")
        self.kristy.lobby[chat]['status'] = 'waiting_start'

    def start_game(self, chat, peer, sender):
        if len(self.kristy.lobby[chat]["players"]) < 2:
            self.kristy.send(peer, "Недостаточно игроков. Минимум 2")
            return
        size_map = self.kristy.lobby[chat]['minigame']["size_map"]
        self.kristy.lobby[chat]['status'] = 'game_playing'
        all_players_vk = self.kristy.vk.users.get(user_ids=self.kristy.lobby[chat]["players"])
        players = {}
        for player in all_players_vk:
            players.update({player["id"]: {
                "name": player["first_name"] + " " + player["last_name"],
                "score": 0
            }})

        self.kristy.send(peer, "Новая мини-игра: \n"
                               "• Название: {0} \n"
                               "• Размер: {1} \n"
                               "• Игроки: \n"
                               "• • {2} \n"
                               "Начало через 10 секунд, приготовьтесь!".format(self.label.upper(),
                                                                               size_map,
                                                                               ' \n• • '.join([player["name"] for player in players.values()])))
        time_end = time.time() + 10
        #############################
        pole: List[List[Cell]] = [[None] * size_map for _ in range(size_map)]
        cells_no_image: List[Cell] = []
        for i in range(size_map):
            for j in range(size_map):
                cell_now = Cell()
                pole[i][j] = cell_now
                cells_no_image.append(cell_now)

        if size_map % 2 == 1:  # удаляет центральный элемент, если это поле нечетное
            pole[size_map // 2][size_map // 2].is_available = False
            cells_no_image.pop(size_map * size_map // 2)

        images_all = os.listdir("anime/icons")
        count_images = size_map * 2
        images_selected = random.SystemRandom().sample(images_all, count_images)

        images_data = {index: image for index, image in enumerate(images_selected)}
        images_list: list = list(images_data.keys())
        while cells_no_image:
            cell_1 = random.SystemRandom().choice(cells_no_image)
            cells_no_image.remove(cell_1)
            cell_2 = random.SystemRandom().choice(cells_no_image)
            cells_no_image.remove(cell_2)

            image_id = random.SystemRandom().choice(images_list)
            images_list.remove(image_id)
            cell_1.image_id = cell_2.image_id = image_id

            if not images_list:
                images_list = list(images_data.keys())

        timed_players = players.copy()
        sequence = []
        for _ in players:
            random_player = list(timed_players.keys())[os.urandom(1)[0] % len(list(timed_players.keys()))]
            sequence.append(random_player)
            timed_players.pop(random_player)

        file_path = draw_pole(pole, images_data)
        uploads = self.kristy.vk_upload.photo_messages(photos=file_path)[0]
        os.remove(file_path)
        pole_image = 'photo{0}_{1}'.format(uploads["owner_id"], uploads["id"])

        time.sleep(time_end - time.time())
        self.kristy.lobby[chat]['time_active'] = time.time() // 60

        self.kristy.minigames.update({
            chat: {
                'name': self.label,
                'players': players,
                'sequence': sequence,
                'pole': pole,
                'images_data': images_data,
                'stack': [],
                'pole_image': pole_image

            }
        })
        self.kristy.send(peer, f"Игра началась. Порядок: {', '.join([self.kristy.minigames[chat]['players'][player]['name'] for player in sequence])}. \n"
                               f"Первым начинает: {players[sequence[0]]['name']}", pole_image)

    def check_game(self, chat, peer, sender, msg):
        msg = msg.lower()
        sequence: list = self.kristy.minigames[chat]["sequence"]
        if sequence[0] != sender:
            return

        if re.findall(r"^([a-h])([12345678])$", msg.strip()):
            shot_y, shot_x = re.findall(r"^([a-h])([12345678])$", msg.strip())[0]
        elif re.findall(r"^([12345678])([a-h])$", msg.strip()):
            shot_x, shot_y = re.findall(r"^([12345678])([a-h])$", msg.strip())[0]
        else:
            return

        size_map = self.kristy.lobby[chat]['minigame']["size_map"]
        pole: List[List[Cell]] = self.kristy.minigames[chat]["pole"]
        images_data = self.kristy.minigames[chat]["images_data"]
        stack: List[Cell] = self.kristy.minigames[chat]["stack"]
        players = self.kristy.minigames[chat]["players"]

        shot_x = int(shot_x) - 1
        shot_y = Column[shot_y].value - 1
        if shot_x + 1 > size_map and shot_y + 1 > size_map:
            return

        if not pole[shot_y][shot_x].is_available:
            self.kristy.send(peer, "Нельзя выбрать эту ячейку")
            return
        if pole[shot_y][shot_x].is_selected:
            self.kristy.send(peer, "Эта ячейка уже выбрана")
            return
        stack.append(pole[shot_y][shot_x])
        pole[shot_y][shot_x].is_selected = True

        file_path = draw_pole(pole, images_data)
        uploads = self.kristy.vk_upload.photo_messages(photos=file_path)[0]
        os.remove(file_path)
        pole_image = 'photo{0}_{1}'.format(uploads["owner_id"], uploads["id"])
        self.kristy.send(peer, f"{players[sequence[0]]['name']} открывает "
                               f"{'первую' if len(stack) == 1 else 'вторую'} ячейку с координатами: {msg.upper()}", pole_image)

        time_end = time.time() + 2  # SLEEEEEEEP 2
        self.kristy.lobby[chat]['time_active'] = time.time() // 60

        if len(stack) == 1:
            return

        cell_1, cell_2 = stack
        stack.clear()
        if cell_1.image_id == cell_2.image_id:
            cell_1.is_available = cell_2.is_available = False

            file_path = draw_pole(pole, images_data)
            uploads = self.kristy.vk_upload.photo_messages(photos=file_path)[0]
            os.remove(file_path)
            pole_image = 'photo{0}_{1}'.format(uploads["owner_id"], uploads["id"])
            self.kristy.minigames[chat]["pole_image"] = pole_image

            time.sleep(time_end - time.time())
            self.kristy.send(peer, f"{players[sequence[0]]['name']} находит две одинаковые ячейки и убирает их с поля. \n"
                                   f"{players[sequence[0]]['name']} ходит ещё раз.", pole_image)

        else:
            cell_1.is_selected = False
            cell_2.is_selected = False

            pole_image = self.kristy.minigames[chat]["pole_image"]

            time.sleep(time_end - time.time())
            self.kristy.send(peer, f"{players[sequence[0]]['name']} промахивается и ход переход другому игроку. \n"
                                   f"Сейчас ходит {players[sequence[1]]['name']}", pole_image)
            sequence.append(sequence.pop(0))




