import ranks
import keyboards
from vkcommands import VKCommand


class ChooseChat(VKCommand):
    def __init__(self, kristy):
        VKCommand.__init__(self, kristy,
                           label='удалить',
                           desc='Открывает меню удаления',
                           usage='???',
                           dm=True)
    def execute(self, chat, peer, sender, args=None, attachments=None, fwd_messages=None):
        self.kristy.send(peer, 'Меню удаления', [], keyboards.delete_keyboard(chat))