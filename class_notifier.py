import threading
import time
from typing import Tuple, Optional, Set, Dict

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
        print('Running')

        for chat in self.kristy.db.all_chat_ids():
            # todo remove
            if chat != 1:
                continue
            # todo remove

            notifications_map: Dict[ClassData, Set[int]] = {}

            for group in self.kristy.db.get_all_groups(chat):
                next_class: Optional[ClassData] = timetable\
                    .next_class(self.kristy.tt_data, chat, [group])

                if next_class is None:
                    continue

                time_until_start: Optional[Tuple[int, int, int]] = timetable\
                    .time_left_raw(self.kristy.tt_data, chat, next_class.start_tstr)

                print(f'    next class for group {group} : "{str(next_class)}", in {time_until_start}')

                if time_until_start is not None and time_until_start[1] == 5:  # 5 минут до начала пары
                    if next_class not in notifications_map:
                        print('      not in map; create new')
                        notifications_map[next_class] = set()

                    notifications_map[next_class].update(self.kristy.db.get_group_members(chat, group))
                    print(f'      len after update: {len(notifications_map[next_class])}')

            print(f'  total map size: {len(notifications_map.keys())}')

            for upcoming_class_data, users_to_mention in notifications_map.items():
                message = '📚 Через 5 минут начнётся %s%s\n\n' \
                          '💡 Не получил(-а) уведомление? Присоединись к группе через меню в ЛС бота!' \
                          % (str(upcoming_class_data), _build_mentions_str(users_to_mention))

                self.kristy.send(peer=2E9+chat, msg=message)

    print()


def _build_mentions_str(users_to_mention: Set[int]) -> str:
    return ''.join([f'[id{user_id}|.]' for user_id in users_to_mention])
