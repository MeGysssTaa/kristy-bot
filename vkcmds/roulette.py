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
        response = "Играем в русскую рулетку. И проиграл у нас: "
        users = self.kristy.db.get_users(chat)
        random_user = users[os.urandom(1)[0] % len(users)]
        user_photo = self.kristy.vk.users.get(user_id=random_user, fields=["photo_id", "photo_max_orig"])[0]
        if not user_photo["is_closed"]:
            self.kristy.send(peer, response, "photo" + user_photo["photo_id"])
        else:
            list_attachments = self.kristy.get_list_attachments([{"type": "photo", "photo": {"sizes": [{"width": 400, "url": user_photo["photo_max_orig"]}]}}], peer)
            self.kristy.send(peer, response, list_attachments)
