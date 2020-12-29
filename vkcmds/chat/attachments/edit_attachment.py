import ranks
from vkcommands import VKCommand


class EditAttachment(VKCommand):
    def __init__(self, kristy):
        VKCommand.__init__(self, kristy,
                           label='вложение*',
                           desc='Изменяет текст и/или вложения, привязанные к уже существующему тегу.',
                           usage='!вложение* <тег> [текст] // Чтобы добавить вложения, прикрепите их к сообщению с командой (максимум 4)',
                           min_args=1,
                           min_rank=ranks.Rank.PRO)

    def execute(self, chat, peer, sender, args=None, attachments=None, fwd_messages=None):
        tag = args[0].lower()
        message = args[1:] if len(args) > 1 else []
        message = ' '.join(message)

        if not message and not attachments:
            self.print_usage(peer)
            return
        if not self.kristy.db.get_attachment(chat, tag):
            self.kristy.send(peer, "Данный тег не найден")
            return

        list_attachments = self.kristy.get_list_attachments(attachments, peer)

        if not list_attachments and not message:
            self.kristy.send(peer, "Не удалось изменить")
            return

        self.kristy.db.edit_attachment(chat, tag, message, list_attachments)
        self.kristy.send(peer, "Успешно изменила вложение")