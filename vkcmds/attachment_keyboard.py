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
        tag = args['argument'] if ('argument' in args and args['argument']) else ""
        attachment = self.kristy.db.get_attachment(chat, tag)

        if attachment:
            self.kristy.send(peer, attachment["message"], attachment["attachments"])
            return

        self.kristy.send(peer, "Ой", keyboards.information_keyboard(chat))