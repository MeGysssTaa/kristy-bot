import threading
import time
import traceback
from typing import Tuple, Optional, Set, Dict, List

import schedule

import log_util
import timetable
import timetable_parser
from kristybot import Kristy
from timetable_parser import ClassData


class KSSExecutor:
    def __init__(self, kristy: Kristy):
        self.logger = log_util.init_logging(__name__)
        self.kristy = kristy
        threading.Thread(target=self._start, name='kss-executor-thread', daemon=True).start()

    def _start(self):
        self.logger.debug('Запуск исполнителя KSS (Kristy Schedule Script) в потоке '
                          + threading.current_thread().getName())

        scheduler = schedule.Scheduler()
        scheduler.every().minute.do(self._run)

        while True:
            scheduler.run_pending()
            time.sleep(1)

    def _run(self):
        for chat in self.kristy.db.all_chat_ids():
            if chat not in self.kristy.tt_data.classes:
                continue  # расписание для этой беседы не подключено

            variables: Dict[str, object] = {}

            for var_name, var_value in self.kristy.tt_data.script_globals[chat].items():
                variables[var_name] = var_value

            week_schedule: Dict[str, List[ClassData]] = self.kristy.tt_data.classes[chat]
            all_groups_members: Dict[str, Set[int]] = {}
            all_chat_members: Set[int] = set()  # только участники беседы, которые состоят хотя бы в одной группе

            for group in self.kristy.db.get_all_groups(chat):
                members = set()
                members.update(self.kristy.db.get_group_members(chat, group))
                all_groups_members[group] = members
                all_chat_members.update(members)

            for weekday in timetable_parser.WEEKDAYS_RU.values():
                weekday_schedule: List[ClassData] = week_schedule[weekday]

                for class_data in weekday_schedule:
                    variables['пара'] = class_data
                    class_targets: Set[int] = set()

                    if class_data.target_groups:
                        for target_group in class_data.target_groups:
                            if target_group in all_groups_members:
                                class_targets.update(all_groups_members[target_group])
                    else:
                        class_targets.update(all_chat_members)

                    variables['пара.упоминание_причастных'] = _build_mentions_str(class_targets)

                    seconds_until_start: Optional[int] = timetable\
                        .time_left_raw_seconds(self.kristy.tt_data, chat, class_data.start_tstr)

                    variables['пара.время_до_начала.всего_час'] \
                        = seconds_until_start // 3600 if seconds_until_start else 0
                    variables['пара.время_до_начала.всего_мин'] \
                        = seconds_until_start // 60 if seconds_until_start else 0
                    variables['пара.время_до_начала.всего_сек'] \
                        = seconds_until_start if seconds_until_start else 0

                    time_until_start: Optional[Tuple[int, int, int]] = timetable \
                        .time_left_raw(self.kristy.tt_data, chat, class_data.start_tstr)

                    variables['пара.время_до_начала.час'] = time_until_start[0] if time_until_start else 0
                    variables['пара.время_до_начала.мин'] = time_until_start[1] if time_until_start else 0
                    variables['пара.время_до_начала.сек'] = time_until_start[2] if time_until_start else 0

                    if class_data.target_groups is None:
                        join_pls = 'любой группе'
                    elif len(class_data.target_groups) == 1:
                        join_pls = 'группе "%s"' % class_data.target_groups[0]
                    else:
                        join_pls = 'группам '

                        for i, target_group in enumerate(class_data.target_groups):
                            if i == 0:
                                join_pls += '"%s"' % target_group
                            else:
                                join_pls += ', "%s"' % target_group

                        join_pls += ' (ко всем или к некоторым)'

                    variables['пара.присоедись_к_группам'] = join_pls

                    for script in class_data.scripts:
                        # noinspection PyBroadException
                        try:
                            script.execute(self.kristy, chat, variables)
                        except Exception:
                            err_msg = '⚠ Ошибка выполнения сценария.\n' \
                                      '\n' \
                                      'День недели: %s\n' \
                                      'Пара: %s\n' \
                                      '\n' \
                                      'Текст сценария:\n' \
                                      '\n' \
                                      '%s\n' \
                                      '\n' \
                                      'Текст ошибки:\n' \
                                      '\n' \
                                      '\n%s\n' \
                                      % (weekday, class_data, script, traceback.format_exc())

                            if self.kristy.tt_data.is_kss_debug_enabled(chat):
                                self.kristy.send(2E9 + chat, err_msg)

                            self.logger.error(err_msg)

            #
            #
            # # Сначала собираем информацию со всех групп, и только потом рассылаем уведомления.
            # # Нужно во избежание повторных пингов участников в некоторых случаях.
            # notifications_map: Dict[ClassData, Set[int]] = {}
            #
            # for group in self.kristy.db.get_all_groups(chat):
            #     next_class: Optional[ClassData] = timetable\
            #         .next_class(self.kristy.tt_data, chat, [group])
            #
            #     if next_class is None or not next_class.notify:
            #         continue  # пар сегодня больше нет, либо для следующей пары этой группы отключены уведомления
            #
            #     time_until_start: Optional[Tuple[int, int, int]] = timetable\
            #         .time_left_raw(self.kristy.tt_data, chat, next_class.start_tstr)
            #
            #     if _should_notify(time_until_start):
            #         if next_class not in notifications_map:
            #             notifications_map[next_class] = set()
            #
            #         notifications_map[next_class].update(self.kristy.db.get_group_members(chat, group))
            #
            # for upcoming_class_data, users_to_mention in notifications_map.items():
            #     self.logger.debug('Отправка уведомления о скором начале пары "%s" '
            #                       'в беседе № %s для %s пользователей...',
            #                       upcoming_class_data, chat, len(users_to_mention))
            #
            #     if upcoming_class_data.target_groups is None:
            #         join_pls = 'любой группе'
            #     elif len(upcoming_class_data.target_groups) == 1:
            #         join_pls = 'группе "%s"' % upcoming_class_data.target_groups[0]
            #     else:
            #         join_pls = 'группам '
            #
            #         for i, target_group in enumerate(upcoming_class_data.target_groups):
            #             if i == 0:
            #                 join_pls += '"%s"' % target_group
            #             else:
            #                 join_pls += ', "%s"' % target_group
            #
            #         join_pls += ' (ко всем или к некоторым)'
            #
            #     message = '📚 Через %s минут начнётся %s%s\n\n' \
            #               '💡 Не получил(-а) уведомление? Присоединись к %s через меню в ЛС бота!' \
            #               % (NOTIFY_TIME, upcoming_class_data, _build_mentions_str(users_to_mention), join_pls)
            #
            #     self.kristy.send(peer=2E9+chat, msg=message)

#
# def _should_notify(time_until_start: Optional[Tuple[int, int, int]]) -> bool:
#     return time_until_start is not None\
#        and time_until_start[0] == 0 \
#        and time_until_start[1] == NOTIFY_TIME


def _build_mentions_str(users_to_mention: Set[int]) -> str:
    return ''.join([f'[id{user_id}|.]' for user_id in users_to_mention])
