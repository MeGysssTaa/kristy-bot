import ranks
import re
from vkcommands import VKCommand


class CreateEmails(VKCommand):
    def __init__(self, kristy):
        VKCommand.__init__(self, kristy,
                           label='почта+',
                           desc='Создаёт новые теги для почты.',
                           usage='!почта+ <тег1> [тег2] ... [тегN]',
                           min_args=1,
                           min_rank=ranks.Rank.PRO)

    def execute(self, chat, peer, sender, args=None, attachments=None):
        tags = list(set(args))
        all_tags = self.kristy.db.all_email_tags(chat)
        created = []
        already_existed = []
        bad_names = []
        for tag in tags:
            tag = tag.lower()
            if tag in all_tags:
                already_existed.append(tag)
            elif re.match(r'[a-zA-Zа-яА-ЯёЁ0-9_]', tag):
                created.append(tag)
                self.kristy.db.create_email(chat, tag)
            else:
                bad_names.append(tag)
        if peer > 2E9:
            name_data = self.kristy.vk.users.get(user_id=sender)[0]
            sender_name = name_data['first_name'] + ' ' + name_data['last_name']
            response = sender_name + '\n'
        else:
            response = ''
        if created:
            response += 'Добавила новые теги для почты: \n➕ '
            response += ' \n➕ '.join(created)
            response += ' \n'

        if already_existed:
            response += 'Эти теги уже используются: \n✔ '
            response += ' \n✔ '.join(already_existed)
            response += ' \n'

        if bad_names:
            response += 'Недопустимые названия: \n⛔ '
            response += ' \n⛔ '.join(bad_names)
            response += ' \n'
        self.kristy.send(peer, response)
