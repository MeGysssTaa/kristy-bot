from vkcommands import VKCommand


class ChooseChat(VKCommand):
    def __init__(self, kristy):
        VKCommand.__init__(self, kristy,
                           label='чек',
                           desc='Показывает название аниме')

    def execute(self, chat, peer, sender, args: str = None, attachments=None, fwd_messages=None):
        if self.kristy.anime[chat]:
            self.kristy.send(peer, self.kristy.anime[chat])
        else:
            self.kristy.send(peer, "Вы не использовали пока что !скрин или !скрин2")

