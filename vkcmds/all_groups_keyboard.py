import ranks
import keyboards
from vkcommands import VKCommand


class ChooseChat(VKCommand):
    def __init__(self, kristy):
        VKCommand.__init__(self, kristy,
                           label='все_группы',
                           desc='Показывает все группы в беседе',
                           usage='???',
                           dm=True)

    def execute(self, chat, peer, sender, args=None, attachments=None):
        existing = self.kristy.db.get_all_groups(chat)
        response = 'Все группы: \n'
        for number, group in enumerate(existing):
            response += str(number + 1) + '. ' + group + ' \n'
        if existing:
            self.kristy.send(peer, response, [], keyboards.start_keyboard(chat))
        else:
            self.kristy.send(peer, 'Не нашла групп в беседе', [], keyboards.start_keyboard(chat))
