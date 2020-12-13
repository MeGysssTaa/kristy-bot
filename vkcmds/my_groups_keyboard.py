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
        print(sender_groups)
        object_groups = self.kristy.db.get_object_all_groups(chat)
        print(object_groups)
        groups = sorted([{"name": group["name"], "count": len(group["members"])} for group in object_groups if group["name"] in sender_groups],
                        key=lambda group: (-group["count"], group["name"]))
        response = 'Ваши группы: \n'
        for number, group in enumerate(groups):
            response += '{0}. {1} ({2}) \n'.format(str(number + 1), group["name"], str(group["count"]))
        if groups:
            self.kristy.send(peer, response, [], keyboards.information_keyboard(chat))
        else:
            self.kristy.send(peer, 'Вы не состоите не в какой из групп', [], keyboards.information_keyboard(chat))