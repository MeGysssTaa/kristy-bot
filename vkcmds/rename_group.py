import re

import ranks
from vkcommands import VKCommand, ALL_MENTIONS


class RenameGroup(VKCommand):
    def __init__(self, kristy):
        VKCommand.__init__(self, kristy,
                           label='переименовать',
                           desc='Меняет название группы.',
                           usage='!переименовать <старое_название> <новое_название>',
                           min_args=2,
                           min_rank=ranks.Rank.MODERATOR)

    def execute(self, chat, peer, sender, args=None, attachments=None):
        name_old = args[0]
        name_new = args[1]

        if name_new in ALL_MENTIONS or len(name_new) < 2 or len(name_new) > 30 or not re.match(r'[a-zA-Zа-яА-ЯёЁ0-9_]',
                                                                                                  name_new):
            self.kristy.send(peer, "Новое название группы является недопустимым: " + name_new)
            return

        existing = self.kristy.db.get_all_groups(chat)

        if name_old not in existing:
            self.kristy.send(peer, "Такой группы нет в базе данных: " + name_old)
            return
        if name_new in existing:
            self.kristy.send(peer, "Такая группа уже есть в базе данных: " + name_new)
            return

        self.kristy.db.rename_group(chat, name_old, name_new)

        if peer > 2E9:
            name_data = self.kristy.vk.users.get(user_id=sender)[0]
            sender_name = name_data['first_name'] + ' ' + name_data['last_name']
            response = sender_name + '\n'
        else:
            response = ''

        response += 'Успешно установила новое название группы: ' + name_new
        self.kristy.send(peer, response)