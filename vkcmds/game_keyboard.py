import ranks
import keyboards
from vkcommands import VKCommand


class ChooseChat(VKCommand):
    def __init__(self, kristy):
        VKCommand.__init__(self, kristy,
                           label='развлечение',
                           desc='Открывает меню игр',
                           usage='???',
                           dm=True)

    def execute(self, chat, peer, sender, args=None, attachments=None):
        self.kristy.send(peer, 'Меню игр', [], keyboards.game_keyboard(chat))