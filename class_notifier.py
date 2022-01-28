import threading
import time
from typing import Tuple

import schedule

import log_util
import timetable
from kristybot import Kristy
from timetable_parser import ClassData

logger = log_util.init_logging(__name__)


class ClassNotifier:
    def __init__(self, kristy: Kristy):
        self.kristy = kristy
        threading.Thread(target=self._start(), name='class-notifier-thread', daemon=True).start()

    def _start(self):
        logger.info('Запуск автоматического информатора о парах в потоке ' + threading.current_thread().getName())
        schedule.every().minute.at(':00').do(self._run)

        while True:
            schedule.run_pending()
            time.sleep(0.49)

    def _run(self):
        for chat in self.kristy.db.all_chat_ids():
            # todo remove
            if chat != 1:
                continue
            # todo remove

            now = timetable.curtime(self.kristy.tt_data, chat)

            if now is None:
                # Данные для этой беседы не были загружены.
                continue

            for group in self.kristy.db.get_all_groups(chat):
                next_class: ClassData = timetable.next_class(self.kristy.tt_data, chat, [group])
                time_until_start: Tuple[int, int, int] = timetable\
                    .time_left_raw(self.kristy.tt_data, chat, next_class.start_tstr)

                if time_until_start is not None and time_until_start[1] == 5:
                    print('5 mins until class')
                    print(str(next_class))
