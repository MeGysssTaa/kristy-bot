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

    def execute(self, chat, peer, sender, args=None, attachments=None, fwd_messages=None):
        object_groups = self.kristy.db.get_object_all_groups(chat)
        groups = sorted([{"name": group["name"], "count": len(group["members"])} for group in object_groups],
                        key=lambda group: (-group["count"], group["name"]))
        response = 'Все группы: \n'
        sender_groups = self.kristy.db.get_user_groups(chat, sender)
        for number, group in enumerate(groups):
            response += '{0}. {1} ({2}) {3}\n'.format(str(number + 1), group["name"], str(group["count"]), '✅ ' if group["name"] in sender_groups else '')
        if groups:
            self.kristy.send(peer, response, [], keyboards.information_keyboard(chat))
        else:
            self.kristy.send(peer, 'Не нашла групп в беседе', [], keyboards.information_keyboard(chat))
