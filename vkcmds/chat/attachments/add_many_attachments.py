import ranks
from vkcommands import VKCommand


class AddManyAttachments(VKCommand):
    def __init__(self, kristy):
        VKCommand.__init__(self, kristy,
                           label='вложение++',
                           desc='Создаёт несколько новых тегов и привязывает к ним вложения',
                           usage='!вложение++ <тег1> [тег2] [тег3] [тег4] // Чтобы добавить вложения, прикрепите их к сообщению с командой (максимум 4)',
                           min_args=1,
                           min_rank=ranks.Rank.PRO)

    def execute(self, chat, peer, sender, args=None, attachments=None, fwd_messages=None):
        tags = set(args)
        created = []
        already_existed = []
        if not attachments or len(tags) > 4:
            self.print_usage(peer)
            return

        for number, tag in enumerate(tags):
            tag = tag.lower()
            if self.kristy.db.get_attachment(chat, tag):
                already_existed.append(tag)
            else:
                if number + 1 > len(attachments):
                    break
                attachment = self.kristy.get_list_attachments([attachments[number]], peer)

                if not attachment:
                    continue
                created.append(tag)
                self.kristy.db.add_attachment(chat, sender, tag, '', attachment)

        if peer > 2E9:
            name_data = self.kristy.vk.users.get(user_id=sender)[0]
            sender_name = name_data['first_name'] + ' ' + name_data['last_name']
            response = sender_name + '\n'
        else:
            response = ''

        if created:
            response += 'Добавила новые теги для вложений: \n➕ '
            response += ' \n➕ '.join(created)
            response += ' \n'

        if already_existed:
            response += 'Эти теги уже используются: \n✔ '
            response += ' \n✔ '.join(already_existed)
            response += ' \n'

        self.kristy.send(peer, response)
