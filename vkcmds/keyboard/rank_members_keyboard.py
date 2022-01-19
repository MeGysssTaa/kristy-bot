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

    def execute(self, chat, peer, sender, args=None, attachments=None, fwd_messages=None):

        users = self.kristy.db.get_users(chat)
        users_vk = self.kristy.vk.users.get(user_ids=users)
        users_sorted = [[user["first_name"] + ' ' + user["last_name"], self.kristy.db.get_user_rank_val(chat, user["id"]), user['is_closed']] for user in sorted(users_vk, key=lambda user: (user["first_name"], user["last_name"]))]

        users_with_rank_sorted = sorted(users_sorted, key=lambda user: user[1], reverse=True)
        king = users_with_rank_sorted[0]
        users_with_rank_sorted = users_with_rank_sorted[1:]
        response = 'KING: {0} {1} \n'.format(king[0], '♿' if not king[2] else '')
        rank_now = ""
        number = 1
        for user in users_with_rank_sorted:
            if ranks.Rank(user[1]).name != rank_now:
                rank_now = ranks.Rank(user[1]).name
                number = 1
                response += "\n{0}: \n".format(rank_now)
            response += '{0}. {1} {2} \n'.format(str(number), user[0], '♿' if not user[2] else '')
            number += 1
        if users_with_rank_sorted:
            self.kristy.send(peer, response, [], keyboards.information_keyboard(chat))
        else:
            self.kristy.send(peer, 'Нет участников в этой беседе', [], keyboards.information_keyboard(chat))
