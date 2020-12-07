import ranks
import keyboards
from vkcommands import VKCommand


class ChooseChat(VKCommand):
    def __init__(self, kristy):
        VKCommand.__init__(self, kristy,
                           label='информация',
                           desc='Открывает меню информации',
                           usage='???',
                           dm=True)
    def execute(self, chat, peer, sender, args=None, attachments=None):
        chat = args['argument'] if ('argument' in args and args['argument']) else chat
        self.kristy.send(peer, 'Меню информации', [], keyboards.information_keyboard(chat))