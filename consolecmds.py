import os
import threading

import timetable


class ConsoleCmdsDispatcher(threading.Thread):
    def __init__(self):
        super(ConsoleCmdsDispatcher, self).__init__()
        self.daemon = True
    def run(self):
        # Список всех аттрибутов. Понадобится дальше для поиска функции по имени (str).
        attrs = globals().copy()

        while True:
            line = input().strip()

            if len(line) == 0:
                continue

            spl = line.split(' ')
            label = spl[0].lower()
            args = spl[1:] if len(spl) > 1 else []

            # Пытаемся найти метод по имени ('cmd_' + label)
            func = attrs.get('cmd_' + label)

            if func is None:
                print('Unknown command')
            else:
                func(line, label, args)


def start():
    """
    Запускает обработчик консольных команд.
    """
    dispatcher = ConsoleCmdsDispatcher()
    dispatcher.start()


def cmd_stop(line, label, args):
    """
    Завершает работу бота.
    """
    # noinspection PyProtectedMember,PyUnresolvedReferences
    os._exit(0)


def cmd_ttreload(line, label, args):
    """
    Перезагружает все файлы с расписаниями.
    """
    print('Перезагрузка всех файлов с расписаниями')
    timetable.load()
