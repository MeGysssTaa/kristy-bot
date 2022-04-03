import datetime
import threading
import time
import traceback
from typing import Optional

import schedule as schedule

import timetable


class MondayCapybara:
    def __init__(self, kristy):
        self.kristy = kristy
        threading.Thread(target=self._start,
                         name='mon-capy-thread', daemon=True).start()

    def _start(self):
        scheduler = schedule.Scheduler()
        scheduler.every().minute.do(self._run)

        while True:
            scheduler.run_pending()
            time.sleep(1)

    def _run(self):
        # noinspection PyBroadException
        try:
            club_id = -206143282  # https://vk.com/chill_capybaras
            posts = self.kristy.vk_user.wall.get(owner_id=club_id, count=10)

            if "is_pinned" in posts["items"][0] and posts["items"][0]["is_pinned"] == 1:
                posts["items"] = posts["items"][1:]

            for post in posts:
                print('\n\n')
                print(post)
                print('\n')

            print('(end)')
        except Exception:
            traceback.print_exc()
        #
        # for chat in self.kristy.db.all_chat_ids():
        #     now: Optional[datetime] = timetable.curtime(self.kristy.tt_data, chat)
        #
        #     if now is None or now.weekday() != 0:  # 0: Понедельник
        #         continue
        #
        #     last_capy_date: Optional[str] = self.kristy.db.get_last_capy_date()
        #     now_str = f'{now.day}.{now.month}.{now.year}'
        #
        #     if last_capy_date == now_str:
        #         continue
        #
        #     # noinspection PyBroadException
        #     try:
        #         self._exec(chat, now_str)
        #     except Exception:
        #         traceback.print_exc()

