import ranks
from vkcommands import VKCommand


class DeleteEmails(VKCommand):
    def __init__(self, kristy):
        VKCommand.__init__(self, kristy,
                           label='почта-',
                           desc='Удаляет теги для почты.',
                           usage='!почта- <тег1> [тег2] ... [тегN]',
                           min_args=1,
                           min_rank=ranks.Rank.MODERATOR)

    def execute(self, chat, peer, sender, args=None, attachments=None):
        tags = args
        all_tags = self.kristy.db.get_all_emails(chat)
        deleted = []
        not_found = []
        for tag in tags:
            tag = tag.lower()
            if tag in all_tags:
                deleted.append(tag)
                self.kristy.db.delete_email(chat, tag)
            else:
                not_found.append(tag)
        if peer > 2E9:
            name_data = self.kristy.vk.users.get(user_id=sender)[0]
            sender_name = name_data['first_name'] + ' ' + name_data['last_name']
            response = sender_name + '\n'
        else:
            response = ''
        if deleted:
            response += 'Успешно удалила теги для почты: \n✖ '
            response += ' \n✖ '.join(deleted)
            response += ' \n'

        if not_found:
            response += 'Не нашла вот эти теги: \n⛔ '
            response += ' \n⛔ '.join(not_found)
            response += ' \n'

        self.kristy.send(peer, response)
