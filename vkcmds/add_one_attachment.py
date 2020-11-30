import ranks
from vkcommands import VKCommand


class AddOneAttachment(VKCommand):
    def __init__(self, kristy):
        VKCommand.__init__(self, kristy,
                           label='вложение+',
                           desc='Создаёт новый тег и привязывает к нему текст и/или вложения.',
                           usage='!вложение+ <тег> [текст] // Чтобы добавить вложения, прикрепите их к сообщению с командой (максимум 4)',
                           min_args=1,
                           min_rank=ranks.Rank.PRO)

    def execute(self, chat, peer, sender, args=None, attachments=None):
        tag = args[0].lower()
        message = args[1:] if len(args) > 1 else []
        message = ' '.join(message)

        if not message and not attachments:
            self.print_usage(peer)
            return
        if self.kristy.db.get_attachment(chat, tag):
            self.kristy.send(peer, "Данный тег используется")
            return

        list_attachments = self.kristy.get_list_attachments(attachments, peer)

        if not list_attachments and not message:
            self.kristy.send(peer, "Не удалось добавить")
            return

        self.kristy.db.add_attachment(chat, sender, tag, message, list_attachments)
        self.kristy.send(peer, "Успешно установила вложение")