import re

import ranks
from vkcommands import VKCommand, ALL_MENTIONS


class AddGroup(VKCommand):
    def __init__(self, kristy):
        VKCommand.__init__(self, kristy,
                           label='группа+',
                           desc='Создать новую группу.',
                           usage='!группа+ <группа1> [группа2] [...] [группаN]',
                           min_args=1,
                           min_rank=ranks.Rank.MODERATOR)

    def execute(self, chat, peer, sender, args=None, attachments=None):
        existing = self.kristy.db.get_all_groups(chat)

        created = []
        bad_names = []
        already_existed = []

        for group in args:
            if 2 <= len(group) <= 30 and re.match(r'[a-zA-Zа-яА-ЯёЁ0-9_]', group) \
                    and group not in ALL_MENTIONS:
                if group not in existing:
                    self.kristy.db.create_group(chat, group, sender)
                    created.append(group)
                else:
                    already_existed.append(group)
            else:
                bad_names.append(group)

        if peer > 2E9:
            name_data = self.kristy.vk.users.get(user_id=sender)[0]
            sender_name = name_data['first_name'] + ' ' + name_data['last_name']
            response = sender_name + '\n'
        else:
            response = ''

        if created:
            response += 'Я зарегистрировала эти группы: \n➕ '
            response += ' \n➕ '.join(created)
            response += ' \n'

        if already_existed:
            response += 'Эти группы уже существуют: \n✔ '
            response += ' \n✔ '.join(already_existed)
            response += ' \n'

        if bad_names:
            response += 'Названия этих групп недопустимы: \n🚫 '
            response += ' \n🚫 '.join(bad_names)
            response += ' \n'

        self.kristy.send(peer, response)
