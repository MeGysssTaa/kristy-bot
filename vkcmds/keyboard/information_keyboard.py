import ranks
import keyboards
from vkcommands import VKCommand


class ChooseChat(VKCommand):
    def __init__(self, kristy):
        VKCommand.__init__(self, kristy,
                           label='информация',
                           desc='Открывает меню информации',
                           usage='???',
                           min_rank=ranks.Rank.GOVNO,
                           dm=True)
    def execute(self, chat, peer, sender, args=None, attachments=None, fwd_messages=None):
        self.kristy.send(peer, 'Меню информации', [], keyboards.information_keyboard(chat))