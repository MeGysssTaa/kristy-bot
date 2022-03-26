import random
import re

from vkcommands import VKCommand

IDS_CAPYBARAS = [-208931251,  # https://vk.com/capybary
                 -162903355,  # https://vk.com/kapibaryanstvo
                 -206744223,  # https://vk.com/capybaraclub
                 -206143282,  # https://vk.com/chill_capybaras
                 -201833277]  # https://vk.com/capyeveryday


class Capybara(VKCommand):
    def __init__(self, kristy):
        VKCommand.__init__(self, kristy,
                           label='капибара',
                           desc='Показывает капибару (sponsored by German)')

    def execute(self, chat, peer, sender, args: str = None, attachments=None, fwd_messages=None):
        for i in range(5):

            random_group_id = random.SystemRandom().choice(IDS_CAPYBARAS)
            posts = self.kristy.vk_user.wall.get(owner_id=random_group_id, count=25)
            if 'is_pinned' in posts["items"][0] and posts["items"][0]["is_pinned"] == 1:
                posts["items"] = posts["items"][1:]
            random_post = random.SystemRandom().choice(posts["items"])
            try:
                data = self.kristy.get_list_attachments(random_post["attachments"], peer)
            except Exception:
                continue
            self.kristy.send(peer, "", attachment=data)
            return
        self.kristy.send(peer, "Видимо сегодня без капибар =(")

