import datetime
import threading
import time
import traceback
from typing import Optional, Tuple

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
            video: Optional[Tuple[str, str]] = self._recent_mon_capy_vid()

            if video is None:
                return

            print('Found the Monday capybara video!!')

            for chat in self.kristy.db.all_chat_ids():
                #todo remove
                if chat != 1:
                    continue
                # todo remove
                self._send_maybe(chat, video[0], video[1])
        except Exception:
            traceback.print_exc()

    def _recent_mon_capy_vid(self) -> Optional[Tuple[str, str]]:
        club_id = -206143282  # https://vk.com/chill_capybaras
        posts = self.kristy.vk_user.wall.get(owner_id=club_id, count=10)

        for post in posts["items"]:
            if "text" not in post or "attachments" not in post:
                continue

            text = post["text"].lower()

            # if "рубрик" not in text \
            #         and "ванн" not in text \
            #         and "таз" not in text \
            #         and "вод" not in text\
            #         and "купа" not in text \
            #         and "понедельн" not in text:
            #     continue

            attachments = post["attachments"]

            for attachment in attachments:
                if "type" in attachment and attachment["type"] == "video":
                    return text, 'video{0}_{1}_{2}'.format(
                        attachment['video']['owner_id'],
                        attachment['video']['id'],
                        attachment['video']['access_key']
                    )

        return None

    def _send_maybe(self, chat: int, text: str, video: str):
        now: Optional[datetime] = timetable.curtime(self.kristy.tt_data, chat)

        if now is None:# or now.weekday() != 0:  # 0: Понедельник
            return

        last_capy_date: Optional[str] = self.kristy.db.get_last_capy_date(chat)
        now_str = f'{now.day}.{now.month}.{now.year}'

        print(f'CHAT {chat} | last capy date : {last_capy_date}, now str : {now_str} -> {last_capy_date == now_str}')

        if last_capy_date == now_str:
            return

        self.kristy.db.set_last_capy_date(chat, now_str)
        self.kristy.send(peer=2E9+chat, msg=text, attachment=[video])
