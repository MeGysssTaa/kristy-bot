import ranks
import keyboards
from vkcommands import VKCommand


class ChooseChat(VKCommand):
    def __init__(self, kristy):
        VKCommand.__init__(self, kristy,
                           label='ранги_участников',
                           desc='Показывает всех участников и их ранг',
                           usage='???',
                           dm=True)

    def execute(self, chat, peer, sender, args=None, attachments=None):

        users = self.kristy.db.get_users(chat)
        users_vk = self.kristy.vk.users.get(user_ids=users)
        users_sorted = [[user["first_name"] + ' ' + user["last_name"], self.kristy.db.get_user_rank_val(chat, user["id"])] for user in sorted(users_vk, key=lambda user: (user["first_name"], user["last_name"]))]
        users_with_rank_sorted = sorted(users_sorted, key=lambda user: user[1], reverse=True)
        response = 'Участники: \n'
        for number, user in enumerate(users_with_rank_sorted):
            response += '{0}. {1} ({2}) \n'.format(str(number + 1), user[0], ranks.Rank(user[1]).name)
        if users_with_rank_sorted:
            self.kristy.send(peer, response, [], keyboards.information_keyboard(chat))
        else:
            self.kristy.send(peer, 'Нет участников в этой беседе', [], keyboards.information_keyboard(chat))