import random
import re

from vkcommands import VKCommand

ID_PETYA = -199227063


class Capybara(VKCommand):
    def __init__(self, kristy):
        VKCommand.__init__(self, kristy,
                           label='петя',
                           desc='Показывает котики говорят доброе утро (sponsored by Petya)')

    def execute(self, chat, peer, sender, args: str = None, attachments=None, fwd_messages=None):
        for i in range(5):
            posts = self.kristy.vk_user.wall.get(owner_id=ID_PETYA, count=1, offset=random.SystemRandom().randint(1, 360))

            # random_post = random.SystemRandom().choice(posts["items"])
            random_post = posts["items"][0]

            try:
                data = self.kristy.get_list_attachments(random_post["attachments"], peer)
            except Exception:
                continue

            self.kristy.send(peer, random_post["text"], attachment=data)
            return

        self.kristy.send(peer, "Видимо сегодня без котиков =(")

