import ranks
import keyboards
from vkcommands import VKCommand


class ChooseChat(VKCommand):
    def __init__(self, kristy):
        VKCommand.__init__(self, kristy,
                           label='стартовая_клавиатура',
                           desc='Отправить стартовую клавиатуру',
                           usage='???',
                           dm=True,
                           min_rank=ranks.Rank.GOVNO)

    def execute(self, chat, peer, sender, args=None, attachments=None, fwd_messages=None):
        chat = args['parameters'][-1] if 'parameters' in args and args['parameters'] else chat
        self.kristy.send(peer, 'Стартовое меню', [], keyboards.start_keyboard(chat))
