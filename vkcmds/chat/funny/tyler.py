import random
import re

from vkcommands import VKCommand

ID_TYLER = -203127230


class Tyler(VKCommand):
    def __init__(self, kristy):
        VKCommand.__init__(self, kristy,
                           label='тайлер',
                           desc='Показывает философию тайлера (sponsored by Matvey)')

    def execute(self, chat, peer, sender, args: str = None, attachments=None, fwd_messages=None):
        for i in range(5):
            posts = self.kristy.vk_user.wall.get(owner_id=ID_TYLER, count=31)

            if 'is_pinned' in posts["items"][0] and posts["items"][0]["is_pinned"] == 1:
                posts["items"] = posts["items"][1:]

            random_post = random.SystemRandom().choice(posts["items"])

            try:
                data = self.kristy.get_list_attachments(random_post["attachments"], peer)
            except Exception:
                continue

            self.kristy.send(peer, random_post["text"], attachment=data)
            return

        self.kristy.send(peer, "Видимо сегодня без тайлера =(")

