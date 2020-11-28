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
        try:
            user_photo = self.kristy.vk.users.get(user_id=random_user, fields=["photo_id"])
            self.kristy.send(peer, response, "photo" + user_photo[0]["photo_id"])
        except:
            self.kristy.send(1 + 2E9, str(user_photo))
