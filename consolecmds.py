import os
import threading

import log_util
from kristybot import Kristy


class ConsoleCmdsDispatcher:
    def __init__(self, kristy: Kristy):
        self.logger = log_util.init_logging(__name__)
        self.kristy = kristy
        threading.Thread(target=self._start, name='console-commands-dispatcher-thread', daemon=True).start()

    def _start(self):
        self.logger.debug('Запуск диспетчера консольных команд в потоке '
                          + threading.current_thread().getName())

        # Список всех аттрибутов класса. Понадобится дальше для поиска функции по имени (str).
        attrs = ConsoleCmdsDispatcher.__dict__

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
                self.logger.warning('Команда не распознана')
            else:
                _func(self, line, label, args)

    def _cmd_help(self, line: str, label: str, args: str):
        """
        Выводит список доступных консольных команд.
        """
        self.logger.info('Доступные консольные команды:')
        attrs = ConsoleCmdsDispatcher.__dict__

        for attr in attrs.keys():
            if attr.startswith('_cmd_') and len(attr) > 5:
                self.logger.info('  %s', attr[5:])

    def _cmd_stop(self, line: str, label: str, args: str):
        """
        Завершает работу бота.
        """
        # noinspection PyProtectedMember,PyUnresolvedReferences
        os._exit(0)

    def _cmd_ttreload(self, line: str, label: str, args: str):
        """
        Перезагружает файл с расписанием указанной беседы.
        """
        if len(args) != 1 or not args[0].isdecimal():
            self.logger.warning('Использование: ttreload <id беседы>')
            return

        self.kristy.tt_data.load_timetable(int(args[0]), hide_errors=True)

    def _cmd_send(self, line: str, label: str, args: str):
        """
        Отправляет сообщение в указанную беседу.
        """
        if len(args) < 2 or not args[0].isdecimal():
            self.logger.warning('Использование: send <id беседы> <текст сообщения>')
            return

        self.kristy.send(peer=2E9+int(args[0]), msg=' '.join(args[1:]))
