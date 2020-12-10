import ranks
import os
from vkcommands import VKCommand


class ChooseMembers(VKCommand):
    def __init__(self, kristy):
        VKCommand.__init__(self, kristy,
                           label='выбор',
                           desc='Выбирает указанное число случайных участников беседы.',
                           usage='!выбор <число_участников>',
                           min_args=1,
                           min_rank=ranks.Rank.PRO)

    def execute(self, chat, peer, sender, args=None, attachments=None):
        number = args[0]

        if not str(number).isdigit() or not int(number) > 0:
            number = 0
        response = "Случайно были выбраны: \n"

        users = self.kristy.db.get_users(chat)
        count = len(users) - int(number)

        for i in range(count):
            users.remove(users[os.urandom(1)[0] % len(users)])
        users_vk = self.kristy.vk.users.get(user_ids=users)
        for number, user in enumerate(users_vk):
            response += str(number + 1) + ". " + user["first_name"] + " " + user[
                "last_name"] + " \n"
        self.kristy.send(peer, response)