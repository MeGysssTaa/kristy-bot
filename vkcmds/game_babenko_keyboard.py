import ranks
import keyboards
from vkcommands import VKCommand


class ChooseChat(VKCommand):
    def __init__(self, kristy):
        VKCommand.__init__(self, kristy,
                           label='игра_бабенко',
                           desc='Открывает игру с Бабенко',
                           usage='???',
                           dm=True)

    def execute(self, chat, peer, sender, args=None, attachments=None):
        self.kristy.send(peer, 'Андрей Бабенко загадал число. Сможете ли вы отгадать его?', [], keyboards.game_babenko_keyboard(chat))