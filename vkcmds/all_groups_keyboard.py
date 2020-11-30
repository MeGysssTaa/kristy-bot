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
        object_groups = self.kristy.db.get_object_groups(chat)
        groups = sorted(sorted([{"name": group["name"], "count": len(group["members"])} for group in object_groups],
                               key=lambda group: group["name"]),
                        key=lambda group: group["count"],
                        reverse=True)
        response = 'Все группы: \n'
        for number, group in enumerate(groups):
            response += '{0}. {1} ({2}) \n'.format(str(number + 1), group["name"], str(group["count"]))
        if groups:
            self.kristy.send(peer, response, [], keyboards.start_keyboard(chat))
        else:
            self.kristy.send(peer, 'Не нашла групп в беседе', [], keyboards.start_keyboard(chat))
