import os

import ranks
from vkcommands import VKCommand


class Roulette(VKCommand):
    def __init__(self, kristy):
        VKCommand.__init__(self, kristy,
                           label='рулетка',
                           desc='Выбирает случайного участника беседы и выводит его фото.',
                           min_rank=ranks.Rank.PRO)

    def execute(self, chat, peer, sender, args=None, attachments=None):

        users = self.kristy.db.get_users(chat)
        random_user = users[os.urandom(1)[0] % len(users)]
        users = self.kristy.vk.users.get(user_ids=[sender, random_user], fields=["photo_id", "photo_max_orig"]).copy()
        imposter, user = users if sender != random_user else users*2
        response = "{0} {1} делает выстрел в:".format(imposter["first_name"], imposter["last_name"])
        if not user["is_closed"] and "photo_id" in user:
            self.kristy.send(peer, response, "photo" + user["photo_id"])
        else:
            list_attachments = self.kristy.get_list_attachments([{"type": "photo", "photo": {"sizes": [{"width": 400, "url": user["photo_max_orig"]}]}}], peer)
            self.kristy.send(peer, response, list_attachments)
