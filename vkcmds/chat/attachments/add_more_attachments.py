import ranks
from vkcommands import VKCommand


class AddOneAttachment(VKCommand):
    def __init__(self, kristy):
        VKCommand.__init__(self, kristy,
                           label='вложение++',
                           desc='Добавляет к вложению, ещё вложения',
                           usage='!вложение++ <тег>// Чтобы добавить вложения, прикрепите их к сообщению с командой (максимум 4)',
                           min_args=1,
                           min_rank=ranks.Rank.PRO)

    def execute(self, chat, peer, sender, args=None, attachments=None, fwd_messages=None):
        tag = args[0].lower()
        message = args[1:] if len(args) > 1 else []
        message = ' '.join(message)

        attachments_db = self.kristy.db.get_attachment(chat, tag)
        if not attachments_db:
            self.kristy.send(peer, "Данный тег не найдён")
            return

        if not attachments:
            self.kristy.send(peer, "Нету новых вложений")
            return

        list_attachments = self.kristy.get_list_attachments(attachments, peer)
        if not list_attachments and not message:
            self.kristy.send(peer, "Вложение не изменено")
            return

        print(attachments_db, list_attachments)
        self.kristy.db.edit_attachment(chat, tag, message, attachments_db["attachments"] + list_attachments)
        self.kristy.send(peer, f"Успешно добавила к тегу '{tag}' новые данные")
