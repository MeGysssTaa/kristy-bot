import keyboards
from vkcommands import VKCommand


class ChooseChat(VKCommand):
    def __init__(self, kristy):
        VKCommand.__init__(self, kristy,
                           label='отключиться',
                           desc='Отключает вас от группы',
                           usage='???',
                           dm=True)

    def execute(self, chat, peer, sender, args=None, attachments=None):
        group = args['parameters'][-1]
        sender_groups = self.kristy.db.get_user_groups(chat, sender)
        if group not in sender_groups:
            self.kristy.send(peer, "Вас нет в этой группе")
        else:
            self.kristy.db.leave_group(chat, group, sender)
            sender_groups.remove(group)
            page_list = args["page_list"]
            object_groups = self.kristy.db.get_object_all_groups(chat)
            groups_sorted = sorted([{"name": group["name"], "count": len(group["members"])} for group in object_groups if group["name"] in sender_groups],
                                   key=lambda group: (-group["count"], group["name"]))
            groups = [{"name": "{0} ({1})".format(group["name"], str(group["count"])),
                       "argument": group["name"],
                       "color": ""} for group in groups_sorted]
            response = "Успешно отключила вас"
            if not groups:
                self.kristy.send(peer, response, [], keyboards.control_keyboard(chat))
            else:
                keyboard = keyboards.choose_keyboard(chat=chat,
                                                     response="",
                                                     buttons=groups,
                                                     page_list=page_list,
                                                     action_now="отключиться_выбор",
                                                     action_to='отключиться',
                                                     action_from='управление')[1]
                self.kristy.send(peer, response, None, keyboard)