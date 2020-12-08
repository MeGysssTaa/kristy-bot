import keyboards
from vkcommands import VKCommand


class ChooseChat(VKCommand):
    def __init__(self, kristy):
        VKCommand.__init__(self, kristy,
                           label='подключиться',
                           desc='Подключает вас к группе',
                           usage='???',
                           dm=True)

    def execute(self, chat, peer, sender, args=None, attachments=None):
        group = args['argument'] if ('argument' in args and args['argument']) else ""
        sender_groups = self.kristy.db.get_user_groups(chat, sender)
        if group in sender_groups:
            self.kristy.send(peer, "Вы уже состоите в этой группе")
        else:
            self.kristy.db.join_group(chat, group, sender)
            page_list = args["page_list"] if "page_list" in args else [0]
            object_groups = self.kristy.db.get_object_all_groups(chat)
            groups_sorted = sorted(sorted([{"name": group["name"], "count": len(group["members"])} for group in object_groups],
                                          key=lambda group: group["name"]),
                                   key=lambda group: group["count"],
                                   reverse=True)
            sender_groups = self.kristy.db.get_user_groups(chat, sender)
            groups = [{"name": "{0} ({1})".format(group["name"], str(group["count"])), "argument": group["name"], "color": ""} for group in groups_sorted if group["name"] not in sender_groups]
            response = "Успешно добавила вас"
            if not groups:
                self.kristy.send(peer, response, [], keyboards.control_keyboard(chat))
            else:
                keyboard = keyboards.choose_keyboard(chat, "", groups, page_list, "подключиться", 'подключиться_выбор', 'управление')[1]
                self.kristy.send(peer, response, None, keyboard)