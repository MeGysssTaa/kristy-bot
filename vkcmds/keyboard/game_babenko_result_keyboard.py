import ranks
import keyboards
from vkcommands import VKCommand


class ChooseChat(VKCommand):
    def __init__(self, kristy):
        VKCommand.__init__(self, kristy,
                           label='игра_бабенко_результат',
                           desc='Результат игры с Бабенко',
                           usage='???',
                           dm=True)

    def execute(self, chat, peer, sender, args=None, attachments=None, fwd_messages=None):
        result = args["result"]
        answer = args["answer"]
        if result:
            self.kristy.send(peer, 'Вы угадали число, которое загадал Андрей Бабенко! Хотите сыграть ещё раз?', [], keyboards.game_babenko_result_keyboard(chat))
        else:
            self.kristy.send(peer, 'Вы не угадали число! Правильное число, которое загадал Андрей Бабенко: {0}. Хотите попытаться ещё раз?'.format(str(answer)), [], keyboards.game_babenko_result_keyboard(chat))