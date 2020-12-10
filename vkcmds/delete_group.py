import ranks
import vkcommands
from vkcommands import VKCommand


class DeleteGroup(VKCommand):
    def __init__(self, kristy):
        VKCommand.__init__(self, kristy,
                           label='удалить',
                           desc='Удалить группу.',
                           usage='!удалить <группа1> [группа2] [...] [группаN]',
                           min_args=1)

    def execute(self, chat, peer, sender, args=None, attachments=None):
        deleted = []
        not_found = []
        not_creator = []

        rank_user = self.kristy.db.get_user_rank(chat, sender)
        existing = self.kristy.db.get_all_groups(chat)
        sender_created_groups = self.kristy.db.get_user_created_groups(chat, sender)

        for group in args:
            if group in existing:
                if group in sender_created_groups or ranks.Rank[rank_user].value >= ranks.Rank.MODERATOR.value:
                    deleted.append(group)
                    self.kristy.db.delete_group(chat, group)
                else:
                    not_creator.append(group)
            else:
                not_found.append(group)

        if peer > 2E9:
            name_data = self.kristy.vk.users.get(user_id=sender)[0]
            sender_name = name_data['first_name'] + ' ' + name_data['last_name']
            response = sender_name + '\n'
        else:
            response = ''

        if deleted:
            response += 'Я удалила эти группы: \n✖ '
            response += ' \n✖ '.join(deleted)
            response += ' \n'

        if not_found:
            response += 'Этих групп и так нет в беседе: \n⛔ '
            response += ' \n⛔ '.join(not_found)
            response += ' \n'

        if not_creator:
            response += 'У вас нет прав, чтобы удалить эти группы: \n🚫 '
            response += ' \n🚫 '.join(not_creator)
            response += ' \n'

        self.kristy.send(peer, response)
