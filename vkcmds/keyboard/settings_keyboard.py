import ranks
import keyboards
from vkcommands import VKCommand


class ChooseChat(VKCommand):
    def __init__(self, kristy):
        VKCommand.__init__(self, kristy,
                           label='настройки',
                           desc='Меню настроек',
                           usage='???',
                           min_rank=ranks.Rank.GOVNO,
                           dm=True)

    def execute(self, chat, peer, sender, args=None, attachments=None):
        self.kristy.send(peer, 'Меню настроек', [], keyboards.settings_keyboard(chat))