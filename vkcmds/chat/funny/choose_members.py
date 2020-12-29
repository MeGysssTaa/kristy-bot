import ranks
import os
from vkcommands import VKCommand


class ChooseMembers(VKCommand):
    def __init__(self, kristy):
        VKCommand.__init__(self, kristy,
                           label='выбор',
                           desc='Выбирает указанное (не обязательно) число случайных участников беседы.',
                           usage='!выбор [число_участников]',
                           min_rank=ranks.Rank.PRO)

    def execute(self, chat, peer, sender, args=None, attachments=None, fwd_messages=None):
        number = args[0] if args and str(args[0]).isdigit() and int(args[0]) > 0 else 1

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