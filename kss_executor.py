import threading
import time
import traceback
from typing import Tuple, Optional, Set, Dict, List

import schedule

import kss
import log_util
import timetable
from kristybot import Kristy
from timetable_parser import ClassData


class KSSExecutor:
    def __init__(self, kristy: Kristy):
        self.logger = log_util.init_logging(__name__)
        self.kristy = kristy
        self.variables: Dict[int, Dict[str, object]] = {}

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

            if chat not in self.variables:
                chat_globals: Dict[str, object] = {}

                for var_name, var_value in self.kristy.tt_data.script_globals[chat].items():
                    chat_globals[var_name] = kss.expand_variables(var_value, chat_globals)

                self.variables[chat] = chat_globals

            variables: Dict[str, object] = self.variables[chat]

            all_groups_members: Dict[str, Set[int]] = {}
            all_chat_members: Set[int] = set()  # только участники беседы, которые состоят хотя бы в одной группе

            for group in self.kristy.db.get_all_groups(chat):
                members = set()
                members.update(self.kristy.db.get_group_members(chat, group))
                all_groups_members[group] = members
                all_chat_members.update(members)

            today_weekday: str = timetable.weekday_ru(self.kristy.tt_data, chat)
            classes_today: List[ClassData] = self.kristy.tt_data.classes[chat][today_weekday]
            today_week: str = timetable.get_week(self.kristy.tt_data, chat)

            for class_data in classes_today:
                if class_data.week is not None and today_week != class_data.week:
                    continue  # эта пара проходит в другую по чётности неделю (не в эту)

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
                                  'Текст ошибки: см. консоль\n' \
                                  % (today_weekday, class_data, script)

                        if self.kristy.tt_data.is_kss_debug_enabled(chat):
                            self.kristy.send(2E9 + chat, err_msg)

                        self.logger.error(err_msg)
                        traceback.print_exc()


def _build_mentions_str(users_to_mention: Set[int]) -> str:
    return ''.join([f'[id{user_id}|.]' for user_id in users_to_mention])
