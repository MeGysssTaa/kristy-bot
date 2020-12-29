from vkcommands import VKCommand


class Imposters(VKCommand):
    def __init__(self, kristy):
        VKCommand.__init__(self, kristy,
                           label='all',
                           desc='Показать топ 5 предателей',
                           usage='!all')

    def execute(self, chat, peer, sender, args=None, attachments=None, fwd_messages=None):
        users = self.kristy.db.get_all_abusers(chat)
        if not users:
            self.kristy.send(peer, "Предателей нет")
        users_new = sorted(users, key=lambda user: user["all"], reverse=True)
        dict_ids = {}
        for number, user in enumerate(users_new):
            if number == 5:
                break
            dict_ids.update({user["user_id"]: user["all"]})
        users_vk = self.kristy.vk.users.get(user_ids=list(dict_ids.keys()))
        response = "Топ 5 предателей по спаму all и подобных команд: \n"
        for number, user in enumerate(users_vk):
            response += str(number + 1) + ". {0} {1}".format(user['first_name'], user['last_name']) + ": " + str(dict_ids[user['id']]) + ' \n'

        self.kristy.send(peer, response)