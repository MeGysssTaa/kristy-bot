import ranks
from vkcommands import VKCommand


class RenameChat(VKCommand):
    def __init__(self, kristy):
        VKCommand.__init__(self, kristy,
                           label='название',
                           desc='Меняет название беседы в базе данных бота.',
                           usage='!название <новое_название>',
                           min_args=1,
                           min_rank=ranks.Rank.ADMIN)

    def execute(self, chat, peer, sender, args=None, attachments=None):
        new_name = args[0]
        if new_name in self.kristy.db.all_chat_names():
            self.kristy.send(peer, "Данное имя используется")
            return
        if new_name.isdigit():
            self.kristy.send(peer, "Новое название не должно состоять только из цифр")
            return
        self.kristy.db.rename_chat(chat, new_name)
        self.kristy.send(peer, "Успешно обновила имя беседы")
