import random
import re

from vkcommands import VKCommand

IDS_CATS = [-124440100,  # https://vk.com/catmedicine
            -95648824,   # https://vk.com/memy_pro_kotow
            -208870661,  # https://vk.com/kotany_university
            -162222621,  # https://vk.com/kotikodio
            -199218437,  # https://vk.com/public199218437
            -122103467,  # https://vk.com/murmewmur
            -152869016,  # https://vk.com/cats_meme
            -159843949,  # https://vk.com/stoklove
            ]


class Capybara(VKCommand):
    def __init__(self, kristy):
        VKCommand.__init__(self, kristy,
                           label='мем',
                           desc='Показывает мем (про котов)')

    def execute(self, chat, peer, sender, args: str = None, attachments=None, fwd_messages=None):
        for i in range(10):
            random_group_id = random.SystemRandom().choice(IDS_CATS)
            posts = self.kristy.vk_user.wall.get(owner_id=random_group_id, count=20)
            if 'is_pinned' in posts["items"][0] and posts["items"][0]["is_pinned"] == 1:
                posts["items"] = posts["items"][1:]

            random_post = random.SystemRandom().choice(posts["items"])

            if 'copyright' in random_post and random_post['copyright']:
                continue

            try:
                data = self.kristy.get_list_attachments(random_post["attachments"], peer)
            except Exception:
                continue

            self.kristy.send(peer, random_post["text"], attachment=data)
            return

        self.kristy.send(peer, "Видимо сегодня без капибар =(")

