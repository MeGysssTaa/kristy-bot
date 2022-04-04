import random
import time

import ranks
from vkcommands import VKCommand


class Rouletton(VKCommand):
    def __init__(self, kristy):
        VKCommand.__init__(self, kristy,
                           label='рулетон',
                           desc='Выбирает случайного участника беседы (кто онлайн либо был меньше 10 секунд) и выводит его фото.',
                           min_rank=ranks.Rank.PRO)

    def execute(self, chat, peer, sender, args=None, attachments=None, fwd_messages=None):
        number = int(args[0]) if args and str(args[0]).isdigit() and 0 < int(args[0]) <= 10 else 10 if args and str(args[0]).isdigit() and int(args[0]) > 10 else 1
        users = self.kristy.db.get_users(chat)
        users = users[:1000] if len(users) > 1000 else users
        users_vk = self.kristy.vk.users.get(user_ids=[sender] + users, fields=["photo_id", "photo_max_orig", "has_photo", "last_seen"]).copy()
        imposter = users_vk[0]
        attachments = []
        users_dict = {}
        while len(attachments) != number and users_vk:
            random_user = random.SystemRandom().choice(users_vk)
            if not random_user["has_photo"] or time.time() - random_user["last_seen"]["time"] >= 10:
                users_vk.remove(random_user)
                continue
            if random_user["id"] not in users_dict:
                if not random_user["is_closed"] and "photo_id" in random_user:
                    photo = "photo" + random_user["photo_id"]
                else:
                    photo = self.kristy.get_list_attachments([{"type": "photo", "photo": {"sizes": [{"width": 400, "url": random_user["photo_max_orig"]}]}}], peer)[0]
                users_dict.update({random_user["id"]: photo})
            else:
                photo = users_dict[random_user["id"]]
            attachments.append(photo)
        if not attachments:
            self.kristy.send(peer, "Похоже все уже спят 🙁 (либо без аватарок)")
            return
        response = "{0} {1} делает {2} в:".format(imposter["first_name"],
                                                  imposter["last_name"],
                                                  "выстрелы" if len(attachments) > 1 else "выстрел")
        self.kristy.send(peer, response, attachments)
