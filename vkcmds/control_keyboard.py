import ranks
import keyboards
from vkcommands import VKCommand


class ChooseChat(VKCommand):
    def __init__(self, kristy):
        VKCommand.__init__(self, kristy,
                           label='управление',
                           desc='Открывает меню управления',
                           usage='???',
                           min_rank=ranks.Rank.GOVNO,
                           dm=True)
    def execute(self, chat, peer, sender, args=None, attachments=None):
        self.kristy.send(peer, 'Меню управления', [], keyboards.control_keyboard(chat))