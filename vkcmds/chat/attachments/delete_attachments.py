import ranks
from vkcommands import VKCommand


class RemoveAttachments(VKCommand):
    def __init__(self, kristy):
        VKCommand.__init__(self, kristy,
                           label='вложение-',
                           desc='Удаляет теги.',
                           usage='!вложение- <тег1> [тег2] ... [тегN]',
                           min_args=1,
                           min_rank=ranks.Rank.PRO)

    def execute(self, chat, peer, sender, args=None, attachments=None, fwd_messages=None):
        tags = args
        deleted = []
        not_found = []
        error = []

        for tag in tags:
            tag = tag.lower()
            attachment = self.kristy.db.get_attachment(chat, tag)
            if attachment:
                if "creator" in attachment and sender == attachment["creator"] or self.kristy.db.get_user_rank_val(chat, sender) >= ranks.Rank.MODERATOR.value:
                    deleted.append(tag)
                    self.kristy.db.remove_attachment(chat, tag)
                else:
                    error.append(tag)
            else:
                not_found.append(tag)

        if peer > 2E9:
            name_data = self.kristy.vk.users.get(user_id=sender)[0]
            sender_name = name_data['first_name'] + ' ' + name_data['last_name']
            response = sender_name + '\n'
        else:
            response = ''

        if deleted:
            response += 'Удалила теги для вложений: \n✖ '
            response += ' \n✖ '.join(deleted)
            response += ' \n'

        if error:
            response += 'У вас нет доступа для удаления тега: \n😡 '
            response += ' \n😡 '.join(error)
            response += ' \n'

        if not_found:
            response += 'Не найдены эти теги: \n⛔ '
            response += ' \n⛔ '.join(not_found)
            response += ' \n'

        self.kristy.send(peer, response)
