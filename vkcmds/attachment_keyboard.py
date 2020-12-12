import ranks
import keyboards
from vkcommands import VKCommand


class ChooseChat(VKCommand):
    def __init__(self, kristy):
        VKCommand.__init__(self, kristy,
                           label='вложение',
                           desc='Показывает вложение',
                           usage='???',
                           dm=True)

    def execute(self, chat, peer, sender, args=None, attachments=None):
        tag = args['parameters'][-1]
        attachment = self.kristy.db.get_attachment(chat, tag)
        if attachment:
            self.kristy.send(peer, attachment["message"], attachment["attachments"])
        else:
            self.kristy.send(peer, "Ой", keyboards.information_keyboard(chat))