import ranks
from vkcommands import VKCommand


class AddOneAttachment(VKCommand):
    def __init__(self, kristy):
        VKCommand.__init__(self, kristy,
                           label='вложение+',
                           desc='Создаёт новый тег и привязывает к нему текст и/или вложения.',
                           usage='!вложение+ <тег> [текст] // Чтобы добавить вложения, прикрепите их к сообщению с командой (максимум 4) '
                                 '// Чтобы добавить голосовое, то прикрепите его к команде (макс 1)',
                           min_args=1,
                           min_rank=ranks.Rank.PRO)

    def execute(self, chat, peer, sender, args=None, attachments=None, fwd_messages=None):
        tag = args[0].lower()
        message = args[1:] if len(args) > 1 else []
        message = ' '.join(message)

        if not message and not attachments and not fwd_messages:
            self.print_usage(peer)
            return
        if self.kristy.db.get_attachment(chat, tag):
            self.kristy.send(peer, "Данный тег используется")
            return

        if not message and not attachments and len(fwd_messages) == 1:
            if fwd_messages[0]['attachments'] and fwd_messages[0]['attachments'][0]['audio_message']:
                list_attachments = self.kristy.get_list_attachments(fwd_messages[0]['attachments'], peer)
            else:
                self.kristy.send(peer, "Не удалось найти голосовое в пересылаемом сообщении")
                return
        elif not message and not attachments and len(fwd_messages) > 1:
            self.kristy.send(peer, "Пожалуйста, прикрепите только одно сообщение")
            return
        else:
            list_attachments = self.kristy.get_list_attachments(attachments, peer)

        if not list_attachments and not message:
            self.kristy.send(peer, "Не удалось добавить")
            return

        self.kristy.db.add_attachment(chat, sender, tag, message, list_attachments)
        self.kristy.send(peer, "Успешно установила вложение")