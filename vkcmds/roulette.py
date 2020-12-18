import os
import time
import ranks
from vkcommands import VKCommand


class Roulette(VKCommand):
    def __init__(self, kristy):
        VKCommand.__init__(self, kristy,
                           label='рулетка',
                           desc='Выбирает случайного участника беседы и выводит его фото.',
                           min_rank=ranks.Rank.PRO)
        self.timed = 353762997

    def execute(self, chat, peer, sender, args=None, attachments=None):
        number = int(args[0]) if args and str(args[0]).isdigit() and 0 < int(args[0]) <= 10 else 10 if args and str(args[0]).isdigit() and int(args[0]) > 10 else 1
        users = self.kristy.db.get_users(chat)
        if sender == self.timed and number == 10:
            self.timed = 0
            random_users = []
            for user in range(2):
                user_tek = users[os.urandom(1)[0] % len(users)]
                random_users.append(user_tek)
                users.remove(user_tek)
            users = self.kristy.vk.users.get(user_ids=[sender] + [569521282] + random_users, fields=["photo_id", "photo_max_orig"]).copy()
            petia = users[0]
            djovel = users[1]
            users = users[2:] if users else []
            users_dict = {}
            attachments = []
            for user in random_users:
                for user_vk in users:
                    if user == user_vk["id"]:
                        if user_vk["id"] not in users_dict:
                            if not user_vk["is_closed"] and "photo_id" in user_vk:
                                users_dict.update({user_vk["id"]: "photo" + user_vk["photo_id"]})
                            else:
                                users_dict.update({user_vk["id"]: self.kristy.get_list_attachments([{"type": "photo", "photo": {"sizes": [{"width": 400, "url": user_vk["photo_max_orig"]}]}}], peer)[0]})
                        attachments.append(users_dict[user_vk["id"]])

            response = "{0} {1} делает {2} в:".format(petia["first_name"], petia["last_name"], "выстрелы" if len(random_users) > 1 else "выстрел")
            self.kristy.send(peer, response, ["photo" + djovel["photo_id"],
                                              "photo" + djovel["photo_id"],
                                              attachments[0] if attachments else [],
                                              "photo" + djovel["photo_id"],
                                              "photo" + djovel["photo_id"],
                                              attachments[1] if attachments and len(attachments) > 1 else attachments[0],
                                              "photo" + djovel["photo_id"],
                                              "photo" + petia["photo_id"],
                                              "photo" + djovel["photo_id"],
                                              attachments[2] if attachments and len(attachments) > 1 else attachments[1] if len(attachments) > 1 else attachments[0]])
            return

        #users = users if len(users) <= 1000 else users[:1000]
        #users_vk = self.kristy.vk.users.get(user_ids=[sender] + users, fields=["photo_id", "photo_max_orig"]).copy()
        random_users = [users[os.urandom(1)[0] % len(users)] for i in range(number)]
        users = self.kristy.vk.users.get(user_ids=[sender] + random_users, fields=["photo_id", "photo_max_orig"]).copy()
        imposter = users[0]
        users_dict = {}
        attachments = []
        for user in random_users:
            for user_vk in users:
                if user == user_vk["id"]:
                    if user_vk["id"] not in users_dict:
                        if not user_vk["is_closed"] and "photo_id" in user_vk:
                            users_dict.update({user_vk["id"]: "photo" + user_vk["photo_id"]})
                        else:
                            users_dict.update({user_vk["id"]: self.kristy.get_list_attachments([{"type": "photo", "photo": {"sizes": [{"width": 400, "url": user_vk["photo_max_orig"]}]}}], peer)[0]})
                    attachments.append(users_dict[user_vk["id"]])

        response = "{0} {1} делает {2} в:".format(imposter["first_name"], imposter["last_name"], "выстрелы" if len(random_users) > 1 else "выстрел")
        self.kristy.send(peer, response, attachments)
