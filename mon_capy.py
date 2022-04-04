import datetime
import threading
import time
import traceback
from typing import Optional, Tuple, List

import schedule as schedule

import log_util
import timetable


class MondayCapybara:
    def __init__(self, kristy):
        self.kristy = kristy
        self.logger = log_util.init_logging(__name__)

        threading.Thread(target=self._start,
                         name="mon-capy-thread", daemon=True).start()

    def _start(self):
        scheduler = schedule.Scheduler()
        scheduler.every(15).minutes.do(self._run)

        while True:
            scheduler.run_pending()
            time.sleep(1)

    def _run(self):
        # noinspection PyBroadException
        try:
            self.logger.debug("Поиск капибар...")
            post: Optional[Tuple[str, str]] = self._recent_capy_vid_post()

            if post is None:
                return

            self.logger.debug("Найдено недавнее видео с капибарами!!")
            self.logger.debug("    Текст поста: %s", post[0])
            self.logger.debug("    Видео: %s", post[1])
            self.logger.debug("Рассылка капибар...")

            for chat in self.kristy.db.all_chat_ids():
                self._send_maybe(chat, post[0], post[1])

            self.logger.debug("Каждому по капибаре!!")
        except Exception:
            traceback.print_exc()

    def _recent_capy_vid_post(self) -> Optional[Tuple[str, str]]:
        club_id = -206143282  # https://vk.com/chill_capybaras
        posts = self.kristy.vk_user.wall.get(owner_id=club_id, count=5)

        for post in posts["items"]:
            if "text" not in post or "attachments" not in post:
                continue

            text = post["text"].lower()
            attachments = post["attachments"]
            keywords = [
                'недел',
                'ванн',
                'таз',
                'понедел',
                'вод',
                'купа'
            ]

            if MondayCapybara._none_in(text, keywords):
                continue

            for attachment in attachments:
                if "type" in attachment and attachment["type"] == "video":
                    video = "video{0}_{1}_{2}".format(
                        attachment["video"]["owner_id"],
                        attachment["video"]["id"],
                        attachment["video"]["access_key"]
                    )

                    return text, video

        return None

    @staticmethod
    def _none_in(haystack: str, needles: List[str]) -> bool:
        for needle in needles:
            if needle in haystack:
                return False

        return True

    def _send_maybe(self, chat: int, text: str, video: str):
        now: Optional[datetime] = timetable.curtime(self.kristy.tt_data, chat)

        if now is None or now.weekday() != 0:  # 0: Понедельник
            self.logger.debug("    Капибара не будет выпущена в беседе № %s: не понедельник (%s)", chat, now)
            return

        last_capy_date: Optional[str] = self.kristy.db.get_last_capy_date(chat)
        now_str = f"{now.day}.{now.month}.{now.year}"

        if last_capy_date == now_str:
            self.logger.debug("    Капибара уже была выпущена в беседе № %s", chat)
            return

        self.logger.debug("    Выпускаем капибару в беседе № %s", chat)
        self.kristy.send(peer=2E9+chat, msg=text, attachment=[video])
        self.kristy.db.set_last_capy_date(chat, now_str)
