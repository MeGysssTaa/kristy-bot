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
        group = args['parameters'][-1] if 'parameters' in args and args['parameters'] else ""
        sender_groups = self.kristy.db.get_user_groups(chat, sender)
        if group in sender_groups:
            self.kristy.send(peer, "Вы уже состоите в этой группе")
        else:
            self.kristy.db.join_group(chat, group, sender)
            page_list = args["page_list"]
            object_groups = self.kristy.db.get_object_all_groups(chat)
            sender_groups = self.kristy.db.get_user_groups(chat, sender)
            groups_sorted = sorted([{"name": group["name"], "count": len(group["members"])} for group in object_groups if group["name"] not in sender_groups],
                                   key=lambda group: (-group["count"], group["name"]))
            groups = [{"name": "{0} ({1})".format(group["name"], str(group["count"])),
                       "argument": group["name"],
                       "color": ""} for group in groups_sorted]
            response = "Успешно добавила вас"
            if not groups:
                self.kristy.send(peer, response, [], keyboards.control_keyboard(chat))
            else:
                keyboard = keyboards.choose_keyboard(chat=chat,
                                                     response="",
                                                     buttons=groups,
                                                     page_list=page_list,
                                                     action_now="подключиться_выбор",
                                                     action_to="подключиться",
                                                     action_from='управление')[1]
                self.kristy.send(peer, response, None, keyboard)