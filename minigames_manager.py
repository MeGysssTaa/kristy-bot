import os
import glob
import pyclbr
import threading
import time
import traceback

GAME_STATUS_PLAYING = ["game_playing", "game_paused"]


class MinigamesManager:
    def __init__(self, kristy):
        self.kristy = kristy
        self.minigames = self._load_minigames()
        threading.Thread(target=self.check_active_lobby, daemon=True).start()

    def _load_minigames(self):
        minigames_submodules = dict()
        # Ищем все подмодули и все классы в них без импорта самих подмодулей.
        for root, dirs, files in os.walk(os.path.join("vkcmds", "chat", "minigames", "games"), topdown=False):
            abs_search_path = os.path.join(os.path.dirname(__file__), root, '*.py')

            for path in glob.glob(abs_search_path):
                submodule_name = os.path.basename(path)[:-3]  # -3 из-за '.py'
                all_classes = pyclbr.readmodule("{0}.{1}".format(root.replace(os.path.sep, '.'), submodule_name))
                # Ищем в подмодуле класс, наследующий Minigame.
                command_classes = {
                    name: info
                    for name, info in all_classes.items()
                    if 'Minigame' in info.super
                }
                if command_classes:  # подходящий класс найден
                    minigames_submodules[(root.replace(os.path.sep, '.'), submodule_name)] = command_classes

        minigames = {}  # экземпляры классов зарегистрированных игр
        # Проходимся по подмодулям игр, инициализируем классы игр в них (для каждой
        # игры создаётся один её экземпляр) и добавляем полученные объекты в список игр.
        for submodule, cmd_classes in minigames_submodules.items():
            submodule_root, submodule_name = submodule
            module = __import__(f'{submodule_root}.{submodule_name}')  # импортируем подмодуль по имени
            for mod in submodule_root.split(".")[1:]:
                module = getattr(module, mod)  # идём до папки
            submodule = getattr(module, submodule_name)  # получаем сам подмодуль
            # Проходимся по всем классам миниигр.
            for game_class_name in cmd_classes:
                # Создаём экземпляр этого класса (инициализируем его) и добавляем в список игр.
                class_instance = getattr(submodule, game_class_name)(self.kristy)
                game_label = class_instance.label
                minigames.update({game_label: class_instance})

        return minigames

    def check_minigame(self, chat, peer, sender, msg):
        if self.kristy.minigames[chat] and sender in self.kristy.minigames[chat]["players"] and self.kristy.lobby[chat]["status"] == "game_playing":
            threading.Thread(target=self.minigames[self.kristy.minigames[chat]["name"]].process_game, args=(chat, peer, sender, msg,), daemon=True).start()

    def check_active_lobby(self):
        while True:
            for chat in self.kristy.lobby:
                if self.kristy.lobby[chat] and self.kristy.lobby[chat]["time_active"] + 60 < time.time() // 60:
                    self.kristy.lobby.update({chat: {}})
                    if self.kristy.minigames[chat]:
                        self.kristy.minigames.update({chat: {}})
                    self.kristy.send(2E9 + chat, "Лобби было удалено из-за неактивности.")

            time.sleep(60 - time.time() % 60)


class Minigame:
    def __init__(self, kristy, label, rules, usage=None, min_args=0):
        self.kristy = kristy
        self.label = label
        self.rules = rules
        self.usage = usage
        self.min_args = min_args

    def print_usage(self, peer):
        if self.usage is not None:
            self.kristy.send(peer, '⚠ Использование: \n' + self.usage)

    def process_game(self, chat, peer, sender, msg):
        try:
            self.check_game(chat, peer, sender, msg)
        except Exception:
            self.kristy.send(peer, traceback.format_exc(), ["photo-199300529_457239560"])
            traceback.print_exc()
        pass

    def select_game(self, chat, peer, sender, args):
        pass

    def start_game(self, chat, peer, sender):
        pass

    def check_game(self, chat, peer, sender, msg):

        pass
