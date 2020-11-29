import ranks
import keyboards
from vkcommands import VKCommand


class ChooseChat(VKCommand):
    def __init__(self, kristy):
        VKCommand.__init__(self, kristy,
                           label='мои_группы',
                           desc='Показывает мои группы в беседе',
                           usage='???',
                           dm=True)

    def execute(self, chat, peer, sender, args=None, attachments=None):
        sender_groups = self.kristy.db.get_user_groups(chat, sender)
        response = 'Ваши группы: \n'
        for number, group in enumerate(sender_groups):
            response += str(number + 1) + '. ' + group + ' \n'
        if sender_groups:
            self.kristy.send(peer, response, [], keyboards.start_keyboard(chat))
        else:
            self.kristy.send(peer, 'Вы не состоите не в какой из групп', [], keyboards.start_keyboard(chat))
