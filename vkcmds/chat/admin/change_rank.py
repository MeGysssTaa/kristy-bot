import ranks
import re
from vkcommands import VKCommand


class ChangeRank(VKCommand):
    def __init__(self, kristy):
        VKCommand.__init__(self, kristy,
                           label='ранг',
                           desc='Изменяет ранг выбранных пользователей.',
                           usage='!ранг <название_ранга> <@юзер1> [@юзер2] ... [@юзерN]',
                           min_args=2,
                           min_rank=ranks.Rank.ADMIN)

    def execute(self, chat, peer, sender, args=None, attachments=None):
        change_to_this_rank = args[0].upper()
        sender_rank = self.kristy.db.get_user_rank_val(chat, sender)
        if change_to_this_rank not in ranks.Rank.__members__:
            self.kristy.send(peer, 'Не найден такой ранг')
            return
        change_rank = ranks.Rank[change_to_this_rank].value
        if sender_rank <= change_rank:
            self.kristy.send(peer, 'У вас нет прав на этот ранг')
            return
        users = set(re.findall(r'\[id(\d+)\|[^]]+\]', ' '.join(args[1:])))
        if not users:
            self.print_usage(peer)
            return
        users_up = []
        users_down = []
        users_eq = []
        users_error = []
        existing_users = self.kristy.db.get_users(chat)
        users = [int(user) for user in users]

        for user in users:
            if user in existing_users:
                user_rank = self.kristy.db.get_user_rank_val(chat, user)
                if change_rank > user_rank:
                    self.kristy.db.change_rank(chat, user, change_to_this_rank)
                    users_up.append(user)
                elif change_rank < user_rank < sender_rank:
                    self.kristy.db.change_rank(chat, user, change_to_this_rank)
                    users_down.append(user)
                else:
                    users_eq.append(user)
            else:
                users_error.append(user)
        all_users_vk = self.kristy.vk.users.get(user_ids=users)
        if peer > 2E9:
            name_data = self.kristy.vk.users.get(user_id=sender)[0]
            sender_name = name_data['first_name'] + ' ' + name_data['last_name']
            response = sender_name + '\n'
        else:
            response = ''
        # дальше можно описать одним словом: помогите
        if users_up:
            response += "Повышены в ранге до {0}: \n".format(change_to_this_rank)
            for user in users_up:
                for user_vk in all_users_vk:  # да бред, потом чё-нибудь придумаю
                    if user == user_vk["id"]:
                        response += "🔼 {0} {1} \n".format(user_vk["first_name"], user_vk["last_name"])

        if users_down:
            response += "Понижены в ранге до {0}: \n".format(change_to_this_rank)
            for user in users_down:
                for user_vk in all_users_vk:  # да бред, потом чё-нибудь придумаю
                    if user == user_vk["id"]:
                        response += "🔽 {0} {1} \n".format(user_vk["first_name"], user_vk["last_name"])

        if users_eq:
            response += "Ранг не изменён: \n"
            for user in users_eq:
                for user_vk in all_users_vk:  # да бред, потом чё-нибудь придумаю
                    if user == user_vk["id"]:
                        response += "▶ {0} {1} \n".format(user_vk["first_name"], user_vk["last_name"])

        if users_error:
            response += "Пользователи не найдёны: \n"
            for user in users_error:
                for user_vk in all_users_vk:  # да бред, потом чё-нибудь придумаю
                    if user == user_vk["id"]:
                        response += "❌ {0} {1} \n".format(user_vk["first_name"], user_vk["last_name"])

        self.kristy.send(peer, response)