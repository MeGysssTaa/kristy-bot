import os
import time
import ranks
from vkcommands import VKCommand


class Roulette(VKCommand):
    def __init__(self, kristy):
        VKCommand.__init__(self, kristy,
                           label='статус',
                           desc='Показывает рандомный статус пользователя.',
                           min_rank=ranks.Rank.PRO)

    def execute(self, chat, peer, sender, args=None, attachments=None):

        users = self.kristy.db.get_users(chat)
        users = users[:1000] if len(users) > 1000 else users
        users_vk = self.kristy.vk.users.get(user_ids=users, fields=["status"]).copy()
        response = "Угадайте, чей это статус: \n"
        for i in range(len(users_vk)):
            random_user = users_vk[int.from_bytes(os.urandom(2), byteorder='little') % len(users_vk)]
            users_vk.remove(random_user)
            if random_user["status"]:
                response += random_user["status"]
                self.kristy.send(peer, response)
                return
        self.kristy.send(peer, "Статусов нет")

