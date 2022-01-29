import threading
import time
from typing import Tuple, Optional, Set, Dict

import schedule

import log_util
import timetable
from kristybot import Kristy
from timetable_parser import ClassData


NOTIFY_TIME = 5  # за сколько минут до начала пары рассылать уведомления


class ClassNotifier:
    def __init__(self, kristy: Kristy):
        self.logger = log_util.init_logging(__name__)
        self.kristy = kristy
        threading.Thread(target=self._start, name='class-notifier-thread', daemon=True).start()

    def _start(self):
        self.logger.debug('Запуск автоматического информатора о парах в потоке '
                          + threading.current_thread().getName())

        schedule.every().minute.do(self._run)

        while True:
            schedule.run_pending()
            time.sleep(1)

    def _run(self):
        for chat in self.kristy.db.all_chat_ids():
            if chat not in self.kristy.tt_data.notifications \
                    or not self.kristy.tt_data.notifications[chat]:
                continue  # уведомления о предстоящих парах в этой беседе отключены

            # Сначала собираем информацию со всех групп, и только потом рассылаем уведомления.
            # Нужно во избежание повторных пингов участников в некоторых случаях.
            notifications_map: Dict[ClassData, Set[int]] = {}

            for group in self.kristy.db.get_all_groups(chat):
                next_class: Optional[ClassData] = timetable\
                    .next_class(self.kristy.tt_data, chat, [group])

                if next_class is None or not next_class.notify:
                    continue  # пар сегодня больше нет, либо для следующей пары этой группы отключены уведомления

                time_until_start: Optional[Tuple[int, int, int]] = timetable\
                    .time_left_raw(self.kristy.tt_data, chat, next_class.start_tstr)

                if _should_notify(time_until_start):
                    if next_class not in notifications_map:
                        notifications_map[next_class] = set()

                    notifications_map[next_class].update(self.kristy.db.get_group_members(chat, group))

            for upcoming_class_data, users_to_mention in notifications_map.items():
                self.logger.debug('Отправка уведомления о скором начале пары "%s" '
                                  'в беседе № %s для %s пользователей...',
                                  upcoming_class_data, chat, len(users_to_mention))

                if upcoming_class_data.target_groups is None:
                    join_pls = 'любой группе'
                elif len(upcoming_class_data.target_groups) == 1:
                    join_pls = 'группе "%s"' % upcoming_class_data.target_groups[0]
                else:
                    join_pls = 'группам %s'

                    for i, target_group in enumerate(upcoming_class_data.target_groups):
                        if i == 0:
                            join_pls += '"%s"' % target_group
                        else:
                            join_pls += ', "%s"' % target_group

                    join_pls += ' (ко всем или к некоторым)'

                message = '📚 Через %s минут начнётся %s%s\n\n' \
                          '💡 Не получил(-а) уведомление? Присоединись к %s через меню в ЛС бота!' \
                          % (NOTIFY_TIME, upcoming_class_data, _build_mentions_str(users_to_mention), join_pls)

                self.kristy.send(peer=2E9+chat, msg=message)


def _should_notify(time_until_start: Optional[Tuple[int, int, int]]) -> bool:
    return time_until_start is not None\
       and time_until_start[0] == 0 \
       and time_until_start[1] == NOTIFY_TIME


def _build_mentions_str(users_to_mention: Set[int]) -> str:
    return ''.join([f'[id{user_id}|.]' for user_id in users_to_mention])
