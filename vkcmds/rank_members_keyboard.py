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
        king = users_with_rank_sorted[0]
        users_with_rank_sorted = users_with_rank_sorted[1:]
        response = 'Участники: \n KING: {0} \n\n'.format(king[0])
        rank_now = "ADMIN"
        number = 1
        for user in users_with_rank_sorted:
            if ranks.Rank(user[1]).name != rank_now:
                rank_now = ranks.Rank(user[1]).name
                number = 1
                response += "\n{0}: \n".format(rank_now)
            response += '{0}. {1} \n'.format(str(number), user[0])
            number += 1
        if users_with_rank_sorted:
            self.kristy.send(peer, response, [], keyboards.information_keyboard(chat))
        else:
            self.kristy.send(peer, 'Нет участников в этой беседе', [], keyboards.information_keyboard(chat))