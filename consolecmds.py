import os
import threading

import log_util
from kristybot import Kristy


logger = log_util.init_logging(__name__)


class ConsoleCmdsDispatcher:
    def __init__(self, kristy: Kristy):
        self.kristy = kristy
        threading.Thread(target=self._start, name='console-commands-dispatcher-thread', daemon=True).start()

    def _start(self):
        logger.debug('Запуск диспетчера консольных команд в потоке '
                     + threading.current_thread().getName())

        # Список всех аттрибутов. Понадобится дальше для поиска функции по имени (str).
        attrs = globals().copy()

        while True:
            line = input().strip()

            if len(line) == 0:
                continue

            spl = line.split(' ')
            label = spl[0].lower()
            args = spl[1:] if len(spl) > 1 else []

            # Пытаемся найти метод по имени ('_cmd_' + label)
            _func = attrs.get('_cmd_' + label)

            if _func is None:
                logger.warning('Команда не распознана')
            else:
                _func(self.kristy, line, label, args)


def _cmd_help(kristy: Kristy, line: str, label: str, args: str):
    """
    Выводит список доступных консольных команд.
    """
    logger.info('Доступные консольные команды:')
    attrs = globals().copy()

    for attr in attrs.keys():
        if attr.startswith('_cmd_') and len(attr) > 5:
            logger.info('  %s', attr[5:])


def _cmd_stop(kristy: Kristy, line: str, label: str, args: str):
    """
    Завершает работу бота.
    """
    # noinspection PyProtectedMember,PyUnresolvedReferences
    os._exit(0)


def _cmd_ttreload(kristy: Kristy, line: str, label: str, args: str):
    """
    Перезагружает файл с расписанием указанной беседы.
    """
    if len(args) != 1 or not args[0].isdecimal():
        logger.warning('Использование: ttreload <id беседы>')
        return

    kristy.tt_data.load_timetable(int(args[0]), hide_errors=True)
