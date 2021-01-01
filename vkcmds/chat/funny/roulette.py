import os
import time
import ranks
from vkcommands import VKCommand
import antony_modules


class Roulette(VKCommand):
    def __init__(self, kristy):
        VKCommand.__init__(self, kristy,
                           label='рулетка',
                           desc='Выбирает случайного участника беседы и выводит его фото.',
                           min_rank=ranks.Rank.PRO)
        self.check = {}

    def execute(self, chat, peer, sender, args=None, attachments=None, fwd_messages=None):
        number = int(args[0]) if args and str(args[0]).isdigit() and 0 < int(args[0]) <= 10 else 10 if args and str(args[0]).isdigit() and int(args[0]) > 10 else 1
        users = self.kristy.db.get_users(chat)
        users = users[:1000] if len(users) > 1000 else users
        if chat not in self.check:
            self.check.update(({chat: []}))
        print(self.check[chat])
        if sender in self.check[chat]:
            return
        users_vk = self.kristy.vk.users.get(user_ids=[sender] + users, fields=["photo_id", "photo_max_orig", "has_photo"]).copy()
        imposter = users_vk[0]
        if not imposter["has_photo"]:
            self.kristy.send(peer, "Вы не можете использоват рулетку без аватарки")
            return
        attachments = []
        users_dict = {}
        while len(attachments) != number and users_vk:
            random_user = users_vk[os.urandom(1)[0] % len(users_vk)]
            if not random_user["has_photo"]:
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
            if random_user["id"] not in self.check[chat]:
                self.check[chat].append(random_user["id"])
        if not attachments:
            self.kristy.send(peer, "У всех пользователей нет аватарок")
            return
        response = "{0} {1} делает {2} в:".format(imposter["first_name"], imposter["last_name"], "выстрелы" if len(attachments) > 1 else "выстрел")
        self.kristy.send(peer, response, attachments)
